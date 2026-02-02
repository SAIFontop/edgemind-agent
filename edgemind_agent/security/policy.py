"""Security and policy validation layer."""

import re
import logging
from typing import List, Dict, Any, Set, Optional
from enum import Enum


logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk levels for commands and actions."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    FORBIDDEN = "FORBIDDEN"


class SecurityPolicy:
    """Security policy validator for EdgeMind Agent."""

    # Commands that are explicitly forbidden (destructive operations)
    FORBIDDEN_COMMANDS = {
        'rm', 'dd', 'mkfs', 'fdisk', 'parted', 'shred',
        'systemctl poweroff', 'systemctl reboot', 'shutdown',
        'halt', 'reboot', 'init', 'telinit',
        'iptables -F', 'ip link delete', 'ifconfig down'
    }

    # Patterns for dangerous command options/patterns
    FORBIDDEN_PATTERNS = [
        r'rm\s+(-rf|--recursive.*--force)',  # rm -rf
        r'dd\s+.*of=/dev/',  # dd to block devices
        r'>\s*/dev/[sh]d',  # Redirect to block devices
        r'mkfs\.',  # Filesystem creation
        r':(){:|:&};:',  # Fork bomb
        r'wget.*\|\s*sh',  # Pipe wget to shell
        r'curl.*\|\s*sh',  # Pipe curl to shell
        r'chmod\s+777',  # Overly permissive permissions
    ]

    # Whitelist of allowed commands (safe diagnostic and maintenance)
    WHITELISTED_COMMANDS = {
        # System information
        'uname', 'hostname', 'uptime', 'whoami', 'id', 'date',
        'df', 'du', 'free', 'top', 'ps', 'pstree',
        'lsblk', 'lscpu', 'lsmem', 'lsusb', 'lspci',
        
        # Networking diagnostics
        'ping', 'traceroute', 'netstat', 'ss', 'ip addr', 'ip route',
        'ifconfig', 'route', 'dig', 'nslookup', 'host',
        
        # Service management (read-only)
        'systemctl status', 'systemctl is-active', 'systemctl list-units',
        'service status',
        
        # Log viewing
        'journalctl', 'dmesg', 'tail', 'head', 'cat', 'less', 'more',
        'grep', 'awk', 'sed',
        
        # File system (read-only)
        'ls', 'find', 'locate', 'which', 'whereis', 'file', 'stat',
        
        # Package management (info only)
        'apt list', 'apt show', 'apt search', 'dpkg -l', 'dpkg -s',
        
        # Process management (safe)
        'nice', 'renice', 'kill', 'pkill', 'killall',
        
        # Diagnostics
        'strace', 'ltrace', 'lsof', 'fuser',
        'vmstat', 'iostat', 'mpstat', 'sar',
        
        # Basic utilities
        'echo', 'printf', 'wc', 'sort', 'uniq', 'cut', 'paste',
        'tr', 'tee', 'xargs'
    }

    def __init__(self, strict_mode: bool = True):
        """Initialize security policy.
        
        Args:
            strict_mode: If True, only whitelisted commands are allowed.
        """
        self.strict_mode = strict_mode
        logger.info(f"Security policy initialized (strict_mode={strict_mode})")

    def validate_command(self, command: str) -> Dict[str, Any]:
        """Validate a single command against security policies.
        
        Args:
            command: Command string to validate.
            
        Returns:
            Validation result with allowed status and risk level.
        """
        command = command.strip()
        
        # Check if command is empty
        if not command:
            return {
                'allowed': False,
                'risk_level': RiskLevel.LOW.value,
                'reason': 'Empty command',
                'command': command
            }
        
        # Extract base command (first word)
        base_command = command.split()[0]
        
        # Check for forbidden commands
        if base_command in self.FORBIDDEN_COMMANDS or command in self.FORBIDDEN_COMMANDS:
            return {
                'allowed': False,
                'risk_level': RiskLevel.FORBIDDEN.value,
                'reason': f'Command "{base_command}" is explicitly forbidden',
                'command': command
            }
        
        # Check for forbidden patterns
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return {
                    'allowed': False,
                    'risk_level': RiskLevel.FORBIDDEN.value,
                    'reason': f'Command matches forbidden pattern: {pattern}',
                    'command': command
                }
        
        # In strict mode, check whitelist
        if self.strict_mode:
            is_whitelisted = False
            
            # Check if base command is whitelisted
            if base_command in self.WHITELISTED_COMMANDS:
                is_whitelisted = True
            
            # Check if full command matches whitelisted patterns
            for allowed in self.WHITELISTED_COMMANDS:
                if command.startswith(allowed):
                    is_whitelisted = True
                    break
            
            if not is_whitelisted:
                return {
                    'allowed': False,
                    'risk_level': RiskLevel.HIGH.value,
                    'reason': f'Command "{base_command}" not in whitelist',
                    'command': command
                }
        
        # Assess risk level for allowed commands
        risk_level = self._assess_risk_level(command)
        
        return {
            'allowed': True,
            'risk_level': risk_level.value,
            'reason': 'Command passed security validation',
            'command': command
        }

    def _assess_risk_level(self, command: str) -> RiskLevel:
        """Assess the risk level of an allowed command.
        
        Args:
            command: Command to assess.
            
        Returns:
            Risk level enum.
        """
        base_command = command.split()[0]
        
        # Read-only commands are low risk
        readonly_commands = {
            'ls', 'cat', 'less', 'more', 'head', 'tail', 'grep',
            'find', 'locate', 'which', 'stat', 'file',
            'ps', 'top', 'free', 'df', 'du', 'uptime',
            'systemctl status', 'systemctl is-active',
            'journalctl', 'dmesg'
        }
        
        if base_command in readonly_commands:
            return RiskLevel.LOW
        
        # Process management commands are medium risk
        process_commands = {'kill', 'pkill', 'killall', 'nice', 'renice'}
        if base_command in process_commands:
            return RiskLevel.MEDIUM
        
        # Network commands can be medium to high risk
        network_commands = {'ping', 'traceroute', 'netstat', 'ss'}
        if base_command in network_commands:
            return RiskLevel.MEDIUM
        
        # Default to medium risk for other allowed commands
        return RiskLevel.MEDIUM

    def validate_action_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Validate an entire action plan from the AI.
        
        Args:
            plan: Action plan from the AI brain.
            
        Returns:
            Validation result with details for each step.
        """
        if 'plan' not in plan:
            return {
                'valid': False,
                'reason': 'Invalid plan format: missing "plan" key',
                'validated_steps': []
            }
        
        validated_steps = []
        all_allowed = True
        highest_risk = RiskLevel.LOW
        
        for step in plan['plan']:
            commands = step.get('commands', [])
            step_validation = {
                'step': step.get('step', 0),
                'description': step.get('description', ''),
                'commands': []
            }
            
            for command in commands:
                validation = self.validate_command(command)
                step_validation['commands'].append(validation)
                
                if not validation['allowed']:
                    all_allowed = False
                
                # Track highest risk level
                risk = RiskLevel[validation['risk_level']]
                if risk.value > highest_risk.value:
                    highest_risk = risk
            
            validated_steps.append(step_validation)
        
        return {
            'valid': all_allowed,
            'highest_risk': highest_risk.value,
            'validated_steps': validated_steps,
            'requires_approval': highest_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        }

    def add_to_whitelist(self, command: str) -> bool:
        """Add a command to the whitelist (requires admin approval in production).
        
        Args:
            command: Command to add to whitelist.
            
        Returns:
            True if added successfully.
        """
        if command not in self.FORBIDDEN_COMMANDS:
            self.WHITELISTED_COMMANDS.add(command)
            logger.warning(f"Command added to whitelist: {command}")
            return True
        else:
            logger.error(f"Cannot whitelist forbidden command: {command}")
            return False

    def get_policy_summary(self) -> Dict[str, Any]:
        """Get a summary of the current security policy.
        
        Returns:
            Summary of policy settings.
        """
        return {
            'strict_mode': self.strict_mode,
            'whitelisted_commands_count': len(self.WHITELISTED_COMMANDS),
            'forbidden_commands_count': len(self.FORBIDDEN_COMMANDS),
            'forbidden_patterns_count': len(self.FORBIDDEN_PATTERNS)
        }

"""
EdgeMind Agent - Whitelist Manager
====================================
Command whitelist manager
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

try:
    import yaml
except ImportError:
    yaml = None


class CommandRisk(Enum):
    """Command risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKED = "blocked"


@dataclass
class WhitelistEntry:
    """Whitelist entry"""
    command: str
    is_pattern: bool
    risk: CommandRisk
    description: str
    category: str
    requires_confirmation: bool = False
    allowed_params: Optional[List[str]] = None
    blocked_params: Optional[List[str]] = None


class WhitelistManager:
    """
    Whitelist Manager
    
    - Load and save lists
    - Validate commands
    - Manage patterns
    """
    
    def __init__(self, whitelist_path: Optional[str] = None):
        """
        Initialize the manager
        
        Args:
            whitelist_path: Path to whitelist file
        """
        self.whitelist_path = whitelist_path
        self.entries: List[WhitelistEntry] = []
        self.blacklist_patterns: List[str] = []
        self.blacklist_keywords: List[str] = []
        
        if whitelist_path:
            self.load(whitelist_path)
    
    def load(self, path: str) -> bool:
        """
        Load list from file
        
        Args:
            path: File path
        
        Returns:
            Load success
        """
        if yaml is None:
            return False
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                return False
            
            self.entries = []
            
            for category, commands in data.items():
                if category == "blacklist":
                    self.blacklist_patterns = commands.get("patterns", [])
                    self.blacklist_keywords = commands.get("keywords", [])
                    continue
                
                if not isinstance(commands, list):
                    continue
                
                for cmd_data in commands:
                    if isinstance(cmd_data, dict):
                        # Determine command type
                        is_pattern = "command_pattern" in cmd_data
                        command = cmd_data.get("command_pattern") or cmd_data.get("command", "")
                        
                        entry = WhitelistEntry(
                            command=command,
                            is_pattern=is_pattern,
                            risk=CommandRisk(cmd_data.get("risk", "medium")),
                            description=cmd_data.get("description", ""),
                            category=category,
                            requires_confirmation=cmd_data.get("requires_confirmation", False),
                            allowed_params=cmd_data.get("allowed_params"),
                            blocked_params=cmd_data.get("blocked_paths", cmd_data.get("blocked_files"))
                        )
                        self.entries.append(entry)
            
            return True
            
        except Exception as e:
            print(f"Error loading whitelist: {e}")
            return False
    
    def is_blacklisted(self, command: str) -> Tuple[bool, str]:
        """
        Check if command is blacklisted
        
        Args:
            command: Command to check
        
        Returns:
            (blocked, reason)
        """
        command_lower = command.lower()
        
        # Check patterns
        for pattern in self.blacklist_patterns:
            if pattern.lower() in command_lower:
                return True, f"Matches blacklist pattern: {pattern}"
        
        # Check keywords
        for keyword in self.blacklist_keywords:
            if keyword.lower() in command_lower:
                return True, f"Contains blacklisted keyword: {keyword}"
        
        return False, ""
    
    def find_matching_entry(self, command: str) -> Optional[WhitelistEntry]:
        """
        Find matching entry
        
        Args:
            command: Command to search for
        
        Returns:
            Matching entry or None
        """
        command_stripped = command.strip()
        
        for entry in self.entries:
            if entry.is_pattern:
                # Convert pattern to regex
                regex_pattern = re.sub(r'\{[^}]+\}', r'(.+)', entry.command)
                if re.match(f"^{regex_pattern}$", command_stripped, re.IGNORECASE):
                    return entry
            else:
                # Direct or prefix match
                if command_stripped.lower().startswith(entry.command.lower()):
                    return entry
        
        return None
    
    def validate(self, command: str) -> Tuple[bool, str, CommandRisk]:
        """
        Validate command
        
        Args:
            command: Command to validate
        
        Returns:
            (valid, reason, risk level)
        """
        # Check blacklist first
        is_blacklisted, reason = self.is_blacklisted(command)
        if is_blacklisted:
            return False, reason, CommandRisk.BLOCKED
        
        # Search in whitelist
        entry = self.find_matching_entry(command)
        
        if entry is None:
            return False, "Command not in whitelist", CommandRisk.BLOCKED
        
        # Check blocked params
        if entry.blocked_params:
            for blocked in entry.blocked_params:
                if blocked.lower() in command.lower():
                    return False, f"Contains blocked parameter: {blocked}", CommandRisk.BLOCKED
        
        return True, entry.description, entry.risk
    
    def get_commands_by_category(self, category: str) -> List[WhitelistEntry]:
        """Get commands by category"""
        return [e for e in self.entries if e.category == category]
    
    def get_commands_by_risk(self, risk: CommandRisk) -> List[WhitelistEntry]:
        """Get commands by risk level"""
        return [e for e in self.entries if e.risk == risk]
    
    def get_all_categories(self) -> List[str]:
        """Get all categories"""
        return list(set(e.category for e in self.entries))
    
    def add_entry(self, entry: WhitelistEntry) -> None:
        """Add new entry"""
        self.entries.append(entry)
    
    def remove_entry(self, command: str) -> bool:
        """Remove entry"""
        for i, entry in enumerate(self.entries):
            if entry.command == command:
                del self.entries[i]
                return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {}
        
        for entry in self.entries:
            if entry.category not in result:
                result[entry.category] = []
            
            cmd_dict = {
                "risk": entry.risk.value,
                "description": entry.description
            }
            
            if entry.is_pattern:
                cmd_dict["command_pattern"] = entry.command
            else:
                cmd_dict["command"] = entry.command
            
            if entry.requires_confirmation:
                cmd_dict["requires_confirmation"] = True
            
            result[entry.category].append(cmd_dict)
        
        if self.blacklist_patterns or self.blacklist_keywords:
            result["blacklist"] = {
                "patterns": self.blacklist_patterns,
                "keywords": self.blacklist_keywords
            }
        
        return result


# For testing
if __name__ == "__main__":
    manager = WhitelistManager()
    
    # Add manual entries for testing
    manager.entries = [
        WhitelistEntry(
            command="uname -a",
            is_pattern=False,
            risk=CommandRisk.LOW,
            description="System information",
            category="system"
        ),
        WhitelistEntry(
            command="systemctl status {service}",
            is_pattern=True,
            risk=CommandRisk.LOW,
            description="Check service status",
            category="services"
        )
    ]
    
    manager.blacklist_patterns = ["rm -rf", "mkfs"]
    
    # Test
    test_commands = [
        "uname -a",
        "systemctl status ssh",
        "rm -rf /",
        "unknown command"
    ]
    
    print("=== Whitelist Validation Test ===")
    for cmd in test_commands:
        valid, reason, risk = manager.validate(cmd)
        status = "✅" if valid else "❌"
        print(f"{status} {cmd}: {risk.value} - {reason}")

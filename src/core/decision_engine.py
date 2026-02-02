"""
EdgeMind Agent - Decision Engine
==================================
Decision and analysis engine
"""

import json
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    """Risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKED = "blocked"


class ExecutionMode(Enum):
    """Execution modes"""
    ADVISORY = "advisory"      # Advice only
    ASSISTED = "assisted"      # Assisted with confirmation
    AUTOMATIC = "automatic"    # Automatic (low risk)
    BLOCKED = "blocked"        # Blocked


class Category(Enum):
    """Task categories"""
    READ = "read"
    DIAGNOSE = "diagnose"
    PLAN = "plan"
    MODIFY = "modify"
    ERROR = "error"


@dataclass
class Decision:
    """System decision"""
    intent: str
    category: Category
    risk: RiskLevel
    diagnosis: str
    plan: List[str]
    commands_proposed: List[str]
    execution_mode: ExecutionMode
    security_note: str
    resource_impact: str
    reversible: bool
    raw_ai_response: Optional[Dict[str, Any]] = None
    validation_errors: List[str] = None
    
    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []
    
    def is_executable(self) -> bool:
        """Can commands be executed?"""
        return (
            self.execution_mode != ExecutionMode.BLOCKED and
            self.risk != RiskLevel.BLOCKED and
            len(self.commands_proposed) > 0 and
            len(self.validation_errors) == 0
        )
    
    def requires_confirmation(self) -> bool:
        """Does it require user confirmation?"""
        return (
            self.risk == RiskLevel.MEDIUM or
            self.execution_mode == ExecutionMode.ASSISTED
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "intent": self.intent,
            "category": self.category.value,
            "risk": self.risk.value,
            "diagnosis": self.diagnosis,
            "plan": self.plan,
            "commands_proposed": self.commands_proposed,
            "execution_mode": self.execution_mode.value,
            "security_note": self.security_note,
            "resource_impact": self.resource_impact,
            "reversible": self.reversible,
            "is_executable": self.is_executable(),
            "requires_confirmation": self.requires_confirmation(),
            "validation_errors": self.validation_errors
        }


class DecisionEngine:
    """
    Decision Engine
    
    Analyzes AI responses and converts them to executable decisions
    with validation and security checks
    """
    
    # Dangerous command patterns
    DANGEROUS_PATTERNS = [
        "rm -rf",
        "rm -r /",
        "mkfs",
        "dd if=",
        ":(){:|:&};:",
        "chmod -R 777",
        "> /dev/sd",
        "mv /* ",
        "| sh",
        "| bash",
        "shutdown",
        "reboot",
        "halt",
        "poweroff",
        "init 0",
        "init 6",
        "iptables -F",
        "/etc/passwd",
        "/etc/shadow",
    ]
    
    # Dangerous keywords
    DANGEROUS_KEYWORDS = [
        "format",
        "destroy",
        "wipe",
        "nuke",
        "delete all",
        "remove all",
    ]
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize the engine
        
        Args:
            strict_mode: Strict mode (rejects any doubt)
        """
        self.strict_mode = strict_mode
    
    def _parse_risk(self, risk_str: str) -> RiskLevel:
        """Parse risk level"""
        risk_map = {
            "low": RiskLevel.LOW,
            "medium": RiskLevel.MEDIUM,
            "high": RiskLevel.HIGH,
            "blocked": RiskLevel.BLOCKED
        }
        return risk_map.get(risk_str.lower(), RiskLevel.HIGH)
    
    def _parse_category(self, category_str: str) -> Category:
        """Parse category"""
        category_map = {
            "read": Category.READ,
            "diagnose": Category.DIAGNOSE,
            "plan": Category.PLAN,
            "modify": Category.MODIFY,
            "error": Category.ERROR
        }
        return category_map.get(category_str.lower(), Category.ERROR)
    
    def _parse_execution_mode(self, mode_str: str) -> ExecutionMode:
        """Parse execution mode"""
        mode_map = {
            "advisory": ExecutionMode.ADVISORY,
            "assisted": ExecutionMode.ASSISTED,
            "automatic": ExecutionMode.AUTOMATIC,
            "blocked": ExecutionMode.BLOCKED
        }
        return mode_map.get(mode_str.lower(), ExecutionMode.BLOCKED)
    
    def _check_command_safety(self, command: str) -> Tuple[bool, str]:
        """
        Check command safety
        
        Args:
            command: Command to check
        
        Returns:
            (safe, rejection reason)
        """
        command_lower = command.lower()
        
        # Check dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.lower() in command_lower:
                return False, f"Contains dangerous pattern: {pattern}"
        
        # Check keywords
        for keyword in self.DANGEROUS_KEYWORDS:
            if keyword.lower() in command_lower:
                return False, f"Contains dangerous keyword: {keyword}"
        
        # Check sudo commands
        if "sudo" in command_lower and self.strict_mode:
            # Only allowed for some commands
            allowed_sudo = [
                "sudo systemctl",
                "sudo apt",
                "sudo cat",
                "sudo tail",
                "sudo head",
                "sudo journalctl"
            ]
            if not any(allowed in command_lower for allowed in allowed_sudo):
                return False, "Unrecognized sudo command in strict mode"
        
        return True, ""
    
    def _validate_commands(
        self, 
        commands: List[str]
    ) -> Tuple[List[str], List[str]]:
        """
        Validate command list
        
        Args:
            commands: List of commands
        
        Returns:
            (valid commands, errors)
        """
        valid_commands = []
        errors = []
        
        for cmd in commands:
            is_safe, reason = self._check_command_safety(cmd)
            if is_safe:
                valid_commands.append(cmd)
            else:
                errors.append(f"Command blocked: '{cmd[:50]}...' - {reason}")
        
        return valid_commands, errors
    
    def _escalate_risk_if_needed(
        self, 
        risk: RiskLevel, 
        commands: List[str]
    ) -> RiskLevel:
        """Escalate risk level if needed"""
        # If includes sudo commands, escalate to medium at least
        for cmd in commands:
            if "sudo" in cmd.lower():
                if risk == RiskLevel.LOW:
                    return RiskLevel.MEDIUM
        
        return risk
    
    def process_ai_response(
        self, 
        ai_response: Dict[str, Any]
    ) -> Decision:
        """
        Process AI response and convert to decision
        
        Args:
            ai_response: AI response (JSON)
        
        Returns:
            Decision
        """
        # Extract values with safe defaults
        intent = ai_response.get("intent", "unknown")
        category_str = ai_response.get("category", "error")
        risk_str = ai_response.get("risk", "high")
        diagnosis = ai_response.get("diagnosis", "No diagnosis provided")
        plan = ai_response.get("plan", [])
        commands_raw = ai_response.get("commands_proposed", [])
        mode_str = ai_response.get("execution_mode", "blocked")
        security_note = ai_response.get("security_note", "")
        resource_impact = ai_response.get("resource_impact", "unknown")
        reversible = ai_response.get("reversible", False)
        
        # Validate commands
        valid_commands, validation_errors = self._validate_commands(commands_raw)
        
        # Parse values
        category = self._parse_category(category_str)
        risk = self._parse_risk(risk_str)
        execution_mode = self._parse_execution_mode(mode_str)
        
        # Escalate risk if needed
        risk = self._escalate_risk_if_needed(risk, valid_commands)
        
        # If high risk, block execution
        if risk == RiskLevel.HIGH:
            execution_mode = ExecutionMode.BLOCKED
            security_note = security_note or "High risk operation blocked automatically"
        
        # If validation errors, block
        if validation_errors and self.strict_mode:
            execution_mode = ExecutionMode.BLOCKED
        
        return Decision(
            intent=intent,
            category=category,
            risk=risk,
            diagnosis=diagnosis,
            plan=plan if isinstance(plan, list) else [plan],
            commands_proposed=valid_commands,
            execution_mode=execution_mode,
            security_note=security_note,
            resource_impact=resource_impact,
            reversible=reversible,
            raw_ai_response=ai_response,
            validation_errors=validation_errors
        )
    
    def create_error_decision(self, error_message: str) -> Decision:
        """Create error decision"""
        return Decision(
            intent="error",
            category=Category.ERROR,
            risk=RiskLevel.BLOCKED,
            diagnosis=error_message,
            plan=[],
            commands_proposed=[],
            execution_mode=ExecutionMode.BLOCKED,
            security_note="An error occurred during processing",
            resource_impact="none",
            reversible=True,
            validation_errors=[error_message]
        )
    
    def create_blocked_decision(self, reason: str) -> Decision:
        """Create blocked decision"""
        return Decision(
            intent="blocked_request",
            category=Category.ERROR,
            risk=RiskLevel.BLOCKED,
            diagnosis=reason,
            plan=[],
            commands_proposed=[],
            execution_mode=ExecutionMode.BLOCKED,
            security_note=reason,
            resource_impact="none",
            reversible=True,
            validation_errors=[reason]
        )


# For direct testing
if __name__ == "__main__":
    engine = DecisionEngine(strict_mode=True)
    
    # Test safe response
    safe_response = {
        "intent": "check memory usage",
        "category": "diagnose",
        "risk": "low",
        "diagnosis": "Checking system memory",
        "plan": ["Check free memory", "Check swap usage"],
        "commands_proposed": ["free -h", "cat /proc/meminfo"],
        "execution_mode": "automatic",
        "security_note": "",
        "resource_impact": "low",
        "reversible": True
    }
    
    decision = engine.process_ai_response(safe_response)
    print("=== Safe Decision ===")
    print(json.dumps(decision.to_dict(), indent=2))
    print(f"Is Executable: {decision.is_executable()}")
    
    # Test dangerous response
    dangerous_response = {
        "intent": "delete files",
        "category": "modify",
        "risk": "high",
        "diagnosis": "User wants to delete files",
        "plan": ["Delete all files"],
        "commands_proposed": ["rm -rf /"],
        "execution_mode": "blocked",
        "security_note": "This is dangerous",
        "resource_impact": "high",
        "reversible": False
    }
    
    decision = engine.process_ai_response(dangerous_response)
    print("\n=== Dangerous Decision ===")
    print(json.dumps(decision.to_dict(), indent=2))
    print(f"Is Executable: {decision.is_executable()}")

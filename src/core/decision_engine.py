"""
EdgeMind Agent - Decision Engine
==================================
محرك القرارات والتحليل
"""

import json
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    """مستويات الخطورة"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKED = "blocked"


class ExecutionMode(Enum):
    """أوضاع التنفيذ"""
    ADVISORY = "advisory"      # نصائح فقط
    ASSISTED = "assisted"      # مساعدة بتأكيد
    AUTOMATIC = "automatic"    # تلقائي (منخفض الخطورة)
    BLOCKED = "blocked"        # ممنوع


class Category(Enum):
    """تصنيفات المهام"""
    READ = "read"
    DIAGNOSE = "diagnose"
    PLAN = "plan"
    MODIFY = "modify"
    ERROR = "error"


@dataclass
class Decision:
    """قرار النظام"""
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
        """هل يمكن تنفيذ الأوامر؟"""
        return (
            self.execution_mode != ExecutionMode.BLOCKED and
            self.risk != RiskLevel.BLOCKED and
            len(self.commands_proposed) > 0 and
            len(self.validation_errors) == 0
        )
    
    def requires_confirmation(self) -> bool:
        """هل يتطلب تأكيد المستخدم؟"""
        return (
            self.risk == RiskLevel.MEDIUM or
            self.execution_mode == ExecutionMode.ASSISTED
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
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
    محرك القرارات
    
    يحلل استجابات AI ويحولها إلى قرارات قابلة للتنفيذ
    مع التحقق من الصحة والأمان
    """
    
    # أنماط الأوامر الخطرة
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
    
    # الكلمات المفتاحية الخطرة
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
        تهيئة المحرك
        
        Args:
            strict_mode: وضع صارم (يرفض أي شك)
        """
        self.strict_mode = strict_mode
    
    def _parse_risk(self, risk_str: str) -> RiskLevel:
        """تحليل مستوى الخطورة"""
        risk_map = {
            "low": RiskLevel.LOW,
            "medium": RiskLevel.MEDIUM,
            "high": RiskLevel.HIGH,
            "blocked": RiskLevel.BLOCKED
        }
        return risk_map.get(risk_str.lower(), RiskLevel.HIGH)
    
    def _parse_category(self, category_str: str) -> Category:
        """تحليل التصنيف"""
        category_map = {
            "read": Category.READ,
            "diagnose": Category.DIAGNOSE,
            "plan": Category.PLAN,
            "modify": Category.MODIFY,
            "error": Category.ERROR
        }
        return category_map.get(category_str.lower(), Category.ERROR)
    
    def _parse_execution_mode(self, mode_str: str) -> ExecutionMode:
        """تحليل وضع التنفيذ"""
        mode_map = {
            "advisory": ExecutionMode.ADVISORY,
            "assisted": ExecutionMode.ASSISTED,
            "automatic": ExecutionMode.AUTOMATIC,
            "blocked": ExecutionMode.BLOCKED
        }
        return mode_map.get(mode_str.lower(), ExecutionMode.BLOCKED)
    
    def _check_command_safety(self, command: str) -> Tuple[bool, str]:
        """
        فحص أمان أمر
        
        Args:
            command: الأمر للفحص
        
        Returns:
            (آمن, سبب الرفض)
        """
        command_lower = command.lower()
        
        # فحص الأنماط الخطرة
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.lower() in command_lower:
                return False, f"Contains dangerous pattern: {pattern}"
        
        # فحص الكلمات المفتاحية
        for keyword in self.DANGEROUS_KEYWORDS:
            if keyword.lower() in command_lower:
                return False, f"Contains dangerous keyword: {keyword}"
        
        # فحص الأوامر بـ sudo
        if "sudo" in command_lower and self.strict_mode:
            # مسموح فقط لبعض الأوامر
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
        التحقق من قائمة الأوامر
        
        Args:
            commands: قائمة الأوامر
        
        Returns:
            (أوامر صالحة, أخطاء)
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
        """رفع مستوى الخطورة إذا لزم"""
        # إذا تضمنت أوامر sudo، رفع إلى medium على الأقل
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
        معالجة استجابة AI وتحويلها إلى قرار
        
        Args:
            ai_response: استجابة AI (JSON)
        
        Returns:
            Decision
        """
        # استخراج القيم مع defaults آمنة
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
        
        # التحقق من الأوامر
        valid_commands, validation_errors = self._validate_commands(commands_raw)
        
        # تحليل القيم
        category = self._parse_category(category_str)
        risk = self._parse_risk(risk_str)
        execution_mode = self._parse_execution_mode(mode_str)
        
        # رفع الخطورة إذا لزم
        risk = self._escalate_risk_if_needed(risk, valid_commands)
        
        # إذا كان عالي الخطورة، حظر التنفيذ
        if risk == RiskLevel.HIGH:
            execution_mode = ExecutionMode.BLOCKED
            security_note = security_note or "High risk operation blocked automatically"
        
        # إذا كانت هناك أخطاء تحقق، حظر
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
        """إنشاء قرار خطأ"""
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
        """إنشاء قرار محظور"""
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


# للاختبار المباشر
if __name__ == "__main__":
    engine = DecisionEngine(strict_mode=True)
    
    # اختبار استجابة آمنة
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
    
    # اختبار استجابة خطرة
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

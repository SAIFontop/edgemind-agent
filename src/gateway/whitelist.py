"""
EdgeMind Agent - Whitelist Manager
====================================
مدير القائمة البيضاء للأوامر
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
    """مستويات خطورة الأوامر"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKED = "blocked"


@dataclass
class WhitelistEntry:
    """إدخال في القائمة البيضاء"""
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
    مدير القائمة البيضاء
    
    - تحميل وحفظ القوائم
    - التحقق من الأوامر
    - إدارة الأنماط
    """
    
    def __init__(self, whitelist_path: Optional[str] = None):
        """
        تهيئة المدير
        
        Args:
            whitelist_path: مسار ملف القائمة البيضاء
        """
        self.whitelist_path = whitelist_path
        self.entries: List[WhitelistEntry] = []
        self.blacklist_patterns: List[str] = []
        self.blacklist_keywords: List[str] = []
        
        if whitelist_path:
            self.load(whitelist_path)
    
    def load(self, path: str) -> bool:
        """
        تحميل القائمة من ملف
        
        Args:
            path: مسار الملف
        
        Returns:
            نجاح التحميل
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
                        # تحديد نوع الأمر
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
        فحص إذا كان الأمر في القائمة السوداء
        
        Args:
            command: الأمر للفحص
        
        Returns:
            (محظور, السبب)
        """
        command_lower = command.lower()
        
        # فحص الأنماط
        for pattern in self.blacklist_patterns:
            if pattern.lower() in command_lower:
                return True, f"Matches blacklist pattern: {pattern}"
        
        # فحص الكلمات المفتاحية
        for keyword in self.blacklist_keywords:
            if keyword.lower() in command_lower:
                return True, f"Contains blacklisted keyword: {keyword}"
        
        return False, ""
    
    def find_matching_entry(self, command: str) -> Optional[WhitelistEntry]:
        """
        البحث عن إدخال مطابق
        
        Args:
            command: الأمر للبحث عنه
        
        Returns:
            الإدخال المطابق أو None
        """
        command_stripped = command.strip()
        
        for entry in self.entries:
            if entry.is_pattern:
                # تحويل النمط إلى regex
                regex_pattern = re.sub(r'\{[^}]+\}', r'(.+)', entry.command)
                if re.match(f"^{regex_pattern}$", command_stripped, re.IGNORECASE):
                    return entry
            else:
                # مطابقة مباشرة أو بداية
                if command_stripped.lower().startswith(entry.command.lower()):
                    return entry
        
        return None
    
    def validate(self, command: str) -> Tuple[bool, str, CommandRisk]:
        """
        التحقق من صلاحية أمر
        
        Args:
            command: الأمر للتحقق
        
        Returns:
            (صالح, السبب, مستوى الخطورة)
        """
        # فحص القائمة السوداء أولاً
        is_blacklisted, reason = self.is_blacklisted(command)
        if is_blacklisted:
            return False, reason, CommandRisk.BLOCKED
        
        # البحث في القائمة البيضاء
        entry = self.find_matching_entry(command)
        
        if entry is None:
            return False, "Command not in whitelist", CommandRisk.BLOCKED
        
        # فحص المعاملات المحظورة
        if entry.blocked_params:
            for blocked in entry.blocked_params:
                if blocked.lower() in command.lower():
                    return False, f"Contains blocked parameter: {blocked}", CommandRisk.BLOCKED
        
        return True, entry.description, entry.risk
    
    def get_commands_by_category(self, category: str) -> List[WhitelistEntry]:
        """الحصول على أوامر حسب الفئة"""
        return [e for e in self.entries if e.category == category]
    
    def get_commands_by_risk(self, risk: CommandRisk) -> List[WhitelistEntry]:
        """الحصول على أوامر حسب مستوى الخطورة"""
        return [e for e in self.entries if e.risk == risk]
    
    def get_all_categories(self) -> List[str]:
        """الحصول على جميع الفئات"""
        return list(set(e.category for e in self.entries))
    
    def add_entry(self, entry: WhitelistEntry) -> None:
        """إضافة إدخال جديد"""
        self.entries.append(entry)
    
    def remove_entry(self, command: str) -> bool:
        """إزالة إدخال"""
        for i, entry in enumerate(self.entries):
            if entry.command == command:
                del self.entries[i]
                return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
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


# للاختبار
if __name__ == "__main__":
    manager = WhitelistManager()
    
    # إضافة إدخالات يدوية للاختبار
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
    
    # اختبار
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

"""
EdgeMind Agent - Tests for Core Components
"""

import pytest
import sys
import os

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.core import DecisionEngine, Decision, RiskLevel, ExecutionMode, Category
from src.core import ContextBuilder


class TestDecisionEngine:
    """اختبارات محرك القرارات"""
    
    def setup_method(self):
        """إعداد الاختبار"""
        self.engine = DecisionEngine(strict_mode=True)
    
    def test_safe_response_processing(self):
        """اختبار معالجة استجابة آمنة"""
        response = {
            "intent": "check memory",
            "category": "diagnose",
            "risk": "low",
            "diagnosis": "Checking system memory",
            "plan": ["Run free command", "Check memory usage"],
            "commands_proposed": ["free -h"],
            "execution_mode": "automatic",
            "security_note": "",
            "resource_impact": "low",
            "reversible": True
        }
        
        decision = self.engine.process_ai_response(response)
        
        assert decision.risk == RiskLevel.LOW
        assert decision.category == Category.DIAGNOSE
        assert decision.is_executable() == True
        assert len(decision.commands_proposed) == 1
    
    def test_dangerous_command_blocked(self):
        """اختبار حظر الأوامر الخطرة"""
        response = {
            "intent": "delete files",
            "category": "modify",
            "risk": "high",
            "diagnosis": "Dangerous operation",
            "plan": ["Delete all files"],
            "commands_proposed": ["rm -rf /"],
            "execution_mode": "assisted",
            "security_note": "",
            "resource_impact": "high",
            "reversible": False
        }
        
        decision = self.engine.process_ai_response(response)
        
        assert decision.execution_mode == ExecutionMode.BLOCKED
        assert decision.is_executable() == False
        assert len(decision.validation_errors) > 0
    
    def test_high_risk_auto_blocked(self):
        """اختبار الحظر التلقائي للخطورة العالية"""
        response = {
            "intent": "something risky",
            "category": "modify",
            "risk": "high",
            "diagnosis": "High risk operation",
            "plan": [],
            "commands_proposed": ["echo test"],
            "execution_mode": "automatic",
            "security_note": "",
            "resource_impact": "high",
            "reversible": False
        }
        
        decision = self.engine.process_ai_response(response)
        
        assert decision.execution_mode == ExecutionMode.BLOCKED
    
    def test_error_decision_creation(self):
        """اختبار إنشاء قرار خطأ"""
        decision = self.engine.create_error_decision("Test error")
        
        assert decision.category == Category.ERROR
        assert decision.is_executable() == False
        assert "Test error" in decision.diagnosis


class TestContextBuilder:
    """اختبارات جامع السياق"""
    
    def setup_method(self):
        """إعداد الاختبار"""
        self.builder = ContextBuilder()
    
    def test_minimal_context(self):
        """اختبار السياق المختصر"""
        context = self.builder.build_minimal()
        
        assert "timestamp" in context
        assert "hostname" in context
    
    def test_hostname(self):
        """اختبار الحصول على اسم المضيف"""
        hostname = self.builder.get_hostname()
        
        assert hostname is not None
        assert len(hostname) > 0
    
    def test_os_info(self):
        """اختبار معلومات نظام التشغيل"""
        os_info = self.builder.get_os_info()
        
        assert "system" in os_info
        assert "release" in os_info


class TestCommandSafety:
    """اختبارات أمان الأوامر"""
    
    def setup_method(self):
        self.engine = DecisionEngine(strict_mode=True)
    
    def test_safe_commands(self):
        """اختبار الأوامر الآمنة"""
        safe_commands = [
            "free -h",
            "df -h",
            "uptime",
            "ps aux",
            "cat /etc/os-release"
        ]
        
        for cmd in safe_commands:
            is_safe, reason = self.engine._check_command_safety(cmd)
            assert is_safe, f"Command '{cmd}' should be safe: {reason}"
    
    def test_dangerous_commands(self):
        """اختبار الأوامر الخطرة"""
        dangerous_commands = [
            "rm -rf /",
            "mkfs.ext4 /dev/sda",
            "dd if=/dev/zero of=/dev/sda",
            ":(){ :|:& };:",
            "chmod -R 777 /"
        ]
        
        for cmd in dangerous_commands:
            is_safe, reason = self.engine._check_command_safety(cmd)
            assert not is_safe, f"Command '{cmd}' should be dangerous"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

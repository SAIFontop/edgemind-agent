"""
EdgeMind Agent - Tests for Validators
"""

import pytest
import sys
import os

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.utils import InputValidator, ResponseValidator, ValidationResult


class TestInputValidator:
    """اختبارات التحقق من المدخلات"""
    
    def test_valid_request(self):
        """اختبار طلب صالح"""
        result = InputValidator.validate_request("ما هي حالة الذاكرة؟")
        
        assert result.valid == True
        assert len(result.errors) == 0
    
    def test_empty_request(self):
        """اختبار طلب فارغ"""
        result = InputValidator.validate_request("")
        
        assert result.valid == False
        assert len(result.errors) > 0
    
    def test_long_request(self):
        """اختبار طلب طويل جداً"""
        long_request = "a" * 6000
        result = InputValidator.validate_request(long_request)
        
        assert result.valid == False
        assert any("too long" in e for e in result.errors)
    
    def test_xss_pattern_detection(self):
        """اختبار كشف أنماط XSS"""
        xss_request = "<script>alert('xss')</script>"
        result = InputValidator.validate_request(xss_request)
        
        assert result.valid == False
        assert any("forbidden" in e.lower() for e in result.errors)
    
    def test_valid_command(self):
        """اختبار أمر صالح"""
        result = InputValidator.validate_command("echo hello")
        
        assert result.valid == True
    
    def test_empty_command(self):
        """اختبار أمر فارغ"""
        result = InputValidator.validate_command("")
        
        assert result.valid == False
    
    def test_command_with_pipe_warning(self):
        """اختبار تحذير الأنبوب"""
        result = InputValidator.validate_command("cat file | grep pattern")
        
        assert result.valid == True
        assert any("pipe" in w.lower() for w in result.warnings)
    
    def test_api_key_validation(self):
        """اختبار التحقق من مفتاح API"""
        # مفتاح صالح
        result = InputValidator.validate_api_key("AIzaSyAbcdefghijklmnop12345")
        assert result.valid == True
        
        # مفتاح فارغ
        result = InputValidator.validate_api_key("")
        assert result.valid == False
        
        # مفتاح قصير
        result = InputValidator.validate_api_key("short")
        assert result.valid == False


class TestResponseValidator:
    """اختبارات التحقق من الاستجابات"""
    
    def test_valid_response(self):
        """اختبار استجابة صالحة"""
        response = {
            "intent": "check memory",
            "category": "diagnose",
            "risk": "low",
            "diagnosis": "Checking memory",
            "execution_mode": "automatic"
        }
        
        result = ResponseValidator.validate_ai_response(response)
        
        assert result.valid == True
    
    def test_missing_fields(self):
        """اختبار حقول مفقودة"""
        response = {
            "intent": "something"
        }
        
        result = ResponseValidator.validate_ai_response(response)
        
        assert result.valid == False
        assert len(result.errors) > 0
    
    def test_invalid_category(self):
        """اختبار تصنيف غير صالح"""
        response = {
            "intent": "test",
            "category": "invalid_category",
            "risk": "low",
            "diagnosis": "test",
            "execution_mode": "automatic"
        }
        
        result = ResponseValidator.validate_ai_response(response)
        
        # يجب أن يكون صالحاً مع تحذير
        assert any("category" in w.lower() for w in result.warnings)
    
    def test_empty_response(self):
        """اختبار استجابة فارغة"""
        result = ResponseValidator.validate_ai_response({})
        
        assert result.valid == False
    
    def test_none_response(self):
        """اختبار استجابة None"""
        result = ResponseValidator.validate_ai_response(None)
        
        assert result.valid == False


class TestSanitization:
    """اختبارات التنظيف"""
    
    def test_output_sanitization(self):
        """اختبار تنظيف المخرجات"""
        dirty_output = "Hello\x00World\nTest"
        clean_output = InputValidator.sanitize_output(dirty_output)
        
        assert "\x00" not in clean_output
        assert "\n" in clean_output
    
    def test_output_truncation(self):
        """اختبار قص المخرجات"""
        long_output = "a" * 100000
        clean_output = InputValidator.sanitize_output(long_output, max_length=1000)
        
        assert len(clean_output) <= 1020  # 1000 + truncation message
        assert "TRUNCATED" in clean_output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

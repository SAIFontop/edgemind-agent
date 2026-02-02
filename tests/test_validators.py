"""
EdgeMind Agent - Tests for Validators
"""

import pytest
import sys
import os

# Add project path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.utils import InputValidator, ResponseValidator, ValidationResult


class TestInputValidator:
    """Input validation tests"""
    
    def test_valid_request(self):
        """Test valid request"""
        result = InputValidator.validate_request("What is the memory status?")
        
        assert result.valid == True
        assert len(result.errors) == 0
    
    def test_empty_request(self):
        """Test empty request"""
        result = InputValidator.validate_request("")
        
        assert result.valid == False
        assert len(result.errors) > 0
    
    def test_long_request(self):
        """Test very long request"""
        long_request = "a" * 6000
        result = InputValidator.validate_request(long_request)
        
        assert result.valid == False
        assert any("too long" in e for e in result.errors)
    
    def test_xss_pattern_detection(self):
        """Test XSS pattern detection"""
        xss_request = "<script>alert('xss')</script>"
        result = InputValidator.validate_request(xss_request)
        
        assert result.valid == False
        assert any("forbidden" in e.lower() for e in result.errors)
    
    def test_valid_command(self):
        """Test valid command"""
        result = InputValidator.validate_command("echo hello")
        
        assert result.valid == True
    
    def test_empty_command(self):
        """Test empty command"""
        result = InputValidator.validate_command("")
        
        assert result.valid == False
    
    def test_command_with_pipe_warning(self):
        """Test pipe warning"""
        result = InputValidator.validate_command("cat file | grep pattern")
        
        assert result.valid == True
        assert any("pipe" in w.lower() for w in result.warnings)
    
    def test_api_key_validation(self):
        """Test API key validation"""
        # Valid key
        result = InputValidator.validate_api_key("AIzaSyAbcdefghijklmnop12345")
        assert result.valid == True
        
        # Empty key
        result = InputValidator.validate_api_key("")
        assert result.valid == False
        
        # Short key
        result = InputValidator.validate_api_key("short")
        assert result.valid == False


class TestResponseValidator:
    """Response validation tests"""
    
    def test_valid_response(self):
        """Test valid response"""
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
        """Test missing fields"""
        response = {
            "intent": "something"
        }
        
        result = ResponseValidator.validate_ai_response(response)
        
        assert result.valid == False
        assert len(result.errors) > 0
    
    def test_invalid_category(self):
        """Test invalid category"""
        response = {
            "intent": "test",
            "category": "invalid_category",
            "risk": "low",
            "diagnosis": "test",
            "execution_mode": "automatic"
        }
        
        result = ResponseValidator.validate_ai_response(response)
        
        # Should be valid with warning
        assert any("category" in w.lower() for w in result.warnings)
    
    def test_empty_response(self):
        """Test empty response"""
        result = ResponseValidator.validate_ai_response({})
        
        assert result.valid == False
    
    def test_none_response(self):
        """Test None response"""
        result = ResponseValidator.validate_ai_response(None)
        
        assert result.valid == False


class TestSanitization:
    """Sanitization tests"""
    
    def test_output_sanitization(self):
        """Test output sanitization"""
        dirty_output = "Hello\x00World\nTest"
        clean_output = InputValidator.sanitize_output(dirty_output)
        
        assert "\x00" not in clean_output
        assert "\n" in clean_output
    
    def test_output_truncation(self):
        """Test output truncation"""
        long_output = "a" * 100000
        clean_output = InputValidator.sanitize_output(long_output, max_length=1000)
        
        assert len(clean_output) <= 1020  # 1000 + truncation message
        assert "TRUNCATED" in clean_output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

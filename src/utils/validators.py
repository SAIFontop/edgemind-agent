"""
EdgeMind Agent - Validators
=============================
Input validation
"""

import re
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Validation result"""
    valid: bool
    errors: List[str]
    warnings: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings
        }


class InputValidator:
    """
    Input validation
    """
    
    # Maximum input length
    MAX_REQUEST_LENGTH = 5000
    MAX_COMMAND_LENGTH = 1000
    
    # Forbidden patterns in requests
    FORBIDDEN_PATTERNS = [
        r'<script',
        r'javascript:',
        r'data:text/html',
        r'on\w+\s*=',  # event handlers
    ]
    
    @staticmethod
    def validate_request(request: str) -> ValidationResult:
        """
        Validate user request
        
        Args:
            request: The request
        
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        
        # Empty check
        if not request or not request.strip():
            errors.append("Request cannot be empty")
            return ValidationResult(False, errors, warnings)
        
        request = request.strip()
        
        # Length check
        if len(request) > InputValidator.MAX_REQUEST_LENGTH:
            errors.append(f"Request too long (max {InputValidator.MAX_REQUEST_LENGTH} chars)")
        
        # Forbidden patterns check
        for pattern in InputValidator.FORBIDDEN_PATTERNS:
            if re.search(pattern, request, re.IGNORECASE):
                errors.append(f"Request contains forbidden pattern")
                break
        
        # Warnings
        if len(request) < 3:
            warnings.append("Request is very short, might not provide enough context")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    @staticmethod
    def validate_command(command: str) -> ValidationResult:
        """
        Validate command
        
        Args:
            command: The command
        
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        
        if not command or not command.strip():
            errors.append("Command cannot be empty")
            return ValidationResult(False, errors, warnings)
        
        command = command.strip()
        
        # Length check
        if len(command) > InputValidator.MAX_COMMAND_LENGTH:
            errors.append(f"Command too long (max {InputValidator.MAX_COMMAND_LENGTH} chars)")
        
        # Unsafe characters check
        unsafe_chars = ['\x00', '\n', '\r']
        for char in unsafe_chars:
            if char in command:
                errors.append("Command contains unsafe characters")
                break
        
        # Warnings
        if '|' in command:
            warnings.append("Command uses pipe, ensure all parts are safe")
        
        if ';' in command:
            warnings.append("Command chains multiple commands")
        
        if '>' in command or '>>' in command:
            warnings.append("Command redirects output")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    @staticmethod
    def validate_api_key(api_key: str) -> ValidationResult:
        """
        Validate API key
        
        Args:
            api_key: The key
        
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        
        if not api_key:
            errors.append("API key is required")
            return ValidationResult(False, errors, warnings)
        
        # Length check
        if len(api_key) < 20:
            errors.append("API key seems too short")
        
        if len(api_key) > 200:
            errors.append("API key seems too long")
        
        # Format check
        if not re.match(r'^[A-Za-z0-9_-]+$', api_key):
            warnings.append("API key contains unusual characters")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> ValidationResult:
        """
        Validate configuration
        
        Args:
            config: Configuration dictionary
        
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        
        # Required fields check
        required_fields = ['general', 'security']
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required config section: {field}")
        
        # Security settings check
        if 'security' in config:
            security = config['security']
            
            if security.get('max_commands_per_session', 0) > 1000:
                warnings.append("max_commands_per_session is very high")
            
            if security.get('command_timeout', 0) > 300:
                warnings.append("command_timeout is very high (>5 min)")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    @staticmethod
    def sanitize_output(output: str, max_length: int = 50000) -> str:
        """
        Sanitize output
        
        Args:
            output: The text
            max_length: Maximum length
        
        Returns:
            Clean text
        """
        if not output:
            return ""
        
        # Remove non-printable characters
        output = ''.join(c for c in output if c.isprintable() or c in '\n\t')
        
        # Truncate length
        if len(output) > max_length:
            output = output[:max_length] + "\n... [TRUNCATED]"
        
        return output


class ResponseValidator:
    """
    AI response validation
    """
    
    REQUIRED_FIELDS = [
        'intent',
        'category',
        'risk',
        'diagnosis',
        'execution_mode'
    ]
    
    VALID_CATEGORIES = ['read', 'diagnose', 'plan', 'modify', 'error']
    VALID_RISKS = ['low', 'medium', 'high', 'blocked']
    VALID_MODES = ['advisory', 'assisted', 'automatic', 'blocked']
    
    @staticmethod
    def validate_ai_response(response: Dict[str, Any]) -> ValidationResult:
        """
        Validate AI response
        
        Args:
            response: The response
        
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        
        if not response:
            errors.append("Response is empty")
            return ValidationResult(False, errors, warnings)
        
        # Required fields check
        for field in ResponseValidator.REQUIRED_FIELDS:
            if field not in response:
                errors.append(f"Missing required field: {field}")
        
        # Valid values check
        if response.get('category') and response['category'] not in ResponseValidator.VALID_CATEGORIES:
            warnings.append(f"Unknown category: {response['category']}")
        
        if response.get('risk') and response['risk'] not in ResponseValidator.VALID_RISKS:
            warnings.append(f"Unknown risk level: {response['risk']}")
        
        if response.get('execution_mode') and response['execution_mode'] not in ResponseValidator.VALID_MODES:
            warnings.append(f"Unknown execution mode: {response['execution_mode']}")
        
        # Commands check
        commands = response.get('commands_proposed', [])
        if commands and not isinstance(commands, list):
            errors.append("commands_proposed must be a list")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


# For testing
if __name__ == "__main__":
    import json
    
    # Test request
    print("=== Request Validation ===")
    tests = [
        "What is the memory status?",
        "",
        "<script>alert('xss')</script>",
        "a" * 6000
    ]
    
    for test in tests:
        result = InputValidator.validate_request(test)
        status = "✅" if result.valid else "❌"
        print(f"{status} '{test[:30]}...' - {result.errors}")
    
    # Test AI response
    print("\n=== AI Response Validation ===")
    valid_response = {
        "intent": "check memory",
        "category": "diagnose",
        "risk": "low",
        "diagnosis": "Checking memory",
        "execution_mode": "automatic"
    }
    
    invalid_response = {
        "intent": "something"
    }
    
    for resp in [valid_response, invalid_response]:
        result = ResponseValidator.validate_ai_response(resp)
        status = "✅" if result.valid else "❌"
        print(f"{status} {json.dumps(resp)[:50]}... - Errors: {result.errors}")

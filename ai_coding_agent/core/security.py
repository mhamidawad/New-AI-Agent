"""Security utilities for input validation and sanitization.

This module provides comprehensive security features including:
- Input validation and sanitization
- API key validation
- File type checking
- Size limits enforcement
- XSS and injection protection
"""

import re
import hashlib
import hmac
import secrets
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import logging

from .types import ValidationResult, SecurityConfig, LanguageType


logger = logging.getLogger(__name__)


class SecurityValidator:
    """Comprehensive security validator for AI Coding Agent."""
    
    def __init__(self, config: SecurityConfig):
        """Initialize security validator with configuration."""
        self.config = config
        
        # Dangerous patterns to detect
        self.dangerous_patterns = [
            # Command injection patterns
            r'[;&|`$(){}[\]<>]',
            r'(?:rm|del|format|sudo|su)\s',
            r'(?:eval|exec|system|shell_exec)\s*\(',
            
            # Path traversal patterns
            r'\.\./',
            r'\.\.\\',
            r'/etc/',
            r'/proc/',
            r'/sys/',
            
            # SQL injection patterns (basic)
            r'(?:union|select|insert|update|delete|drop|alter)\s+',
            r'(?:or|and)\s+\d+\s*=\s*\d+',
            r'[\'"];?\s*(?:or|and|union)',
            
            # Script injection patterns
            r'<script[^>]*>',
            r'javascript:',
            r'onclick\s*=',
            r'onerror\s*=',
        ]
        
        # Compile patterns for performance
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            for pattern in self.dangerous_patterns
        ]
        
        # Allowed characters for different input types
        self.allowed_chars = {
            'filename': re.compile(r'^[a-zA-Z0-9._-]+$'),
            'variable_name': re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$'),
            'safe_text': re.compile(r'^[a-zA-Z0-9\s.,!?()-]+$'),
        }
    
    def validate_input(self, input_data: Any, input_type: str = "general") -> ValidationResult:
        """Validate and sanitize input data.
        
        Args:
            input_data: Data to validate
            input_type: Type of input for specific validation rules
            
        Returns:
            ValidationResult with validation status and sanitized data
        """
        errors = []
        warnings = []
        sanitized_input = input_data
        
        try:
            # Basic type checking
            if input_data is None:
                errors.append("Input cannot be None")
                return ValidationResult(
                    valid=False,
                    errors=errors,
                    warnings=warnings,
                    sanitized_input=None
                )
            
            # Convert to string for validation
            input_str = str(input_data)
            
            # Size validation
            if len(input_str) > self.config.max_input_size:
                errors.append(f"Input too large: {len(input_str)} > {self.config.max_input_size}")
                return ValidationResult(
                    valid=False,
                    errors=errors,
                    warnings=warnings,
                    sanitized_input=None
                )
            
            # Empty input check
            if not input_str.strip():
                errors.append("Input cannot be empty or whitespace only")
                return ValidationResult(
                    valid=False,
                    errors=errors,
                    warnings=warnings,
                    sanitized_input=None
                )
            
            # Dangerous pattern detection
            dangerous_found = self._detect_dangerous_patterns(input_str)
            if dangerous_found:
                errors.extend([f"Dangerous pattern detected: {pattern}" for pattern in dangerous_found])
            
            # Type-specific validation
            type_errors, type_warnings, sanitized_input = self._validate_by_type(
                input_str, input_type
            )
            errors.extend(type_errors)
            warnings.extend(type_warnings)
            
            # Final sanitization if no critical errors
            if not errors and self.config.input_sanitization:
                sanitized_input = self._sanitize_input(sanitized_input, input_type)
            
            is_valid = len(errors) == 0
            
            return ValidationResult(
                valid=is_valid,
                errors=errors,
                warnings=warnings,
                sanitized_input=sanitized_input if is_valid else None
            )
            
        except Exception as e:
            logger.error(f"Error during input validation: {e}")
            return ValidationResult(
                valid=False,
                errors=[f"Validation error: {str(e)}"],
                warnings=warnings,
                sanitized_input=None
            )
    
    def validate_file_path(self, file_path: Union[str, Path]) -> ValidationResult:
        """Validate file path for security issues.
        
        Args:
            file_path: File path to validate
            
        Returns:
            ValidationResult with validation status
        """
        errors = []
        warnings = []
        
        try:
            path_obj = Path(file_path)
            path_str = str(path_obj)
            
            # Basic path validation
            if not path_str:
                errors.append("File path cannot be empty")
                return ValidationResult(valid=False, errors=errors, warnings=warnings)
            
            # Path traversal detection
            if '..' in path_str:
                errors.append("Path traversal detected (..)")
            
            # Absolute path outside allowed areas
            if path_obj.is_absolute():
                warnings.append("Absolute path provided - use caution")
            
            # File extension validation
            suffix = path_obj.suffix.lower()
            if suffix and suffix not in self.config.allowed_file_types:
                errors.append(f"File type not allowed: {suffix}")
            
            # Dangerous file names
            dangerous_names = [
                'con', 'prn', 'aux', 'nul', 'com1', 'com2', 'com3', 'com4',
                'com5', 'com6', 'com7', 'com8', 'com9', 'lpt1', 'lpt2',
                'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'
            ]
            
            if path_obj.stem.lower() in dangerous_names:
                errors.append(f"Dangerous file name: {path_obj.stem}")
            
            # Hidden files warning
            if path_obj.name.startswith('.') and path_obj.name not in ['.env', '.gitignore']:
                warnings.append("Hidden file detected")
            
            is_valid = len(errors) == 0
            
            return ValidationResult(
                valid=is_valid,
                errors=errors,
                warnings=warnings,
                sanitized_input=str(path_obj) if is_valid else None
            )
            
        except Exception as e:
            return ValidationResult(
                valid=False,
                errors=[f"Path validation error: {str(e)}"],
                warnings=warnings,
                sanitized_input=None
            )
    
    def validate_api_key(self, api_key: str, provider: str) -> bool:
        """Validate API key format.
        
        Args:
            api_key: API key to validate
            provider: Provider name (openai, anthropic)
            
        Returns:
            True if API key format is valid
        """
        if not self.config.api_key_validation:
            return True
        
        if not api_key or not isinstance(api_key, str):
            return False
        
        # Remove whitespace
        api_key = api_key.strip()
        
        if provider.lower() == "openai":
            # OpenAI keys typically start with 'sk-' and are 51 chars
            return api_key.startswith('sk-') and len(api_key) >= 20
        
        elif provider.lower() == "anthropic":
            # Anthropic keys typically start with 'sk-ant-'
            return api_key.startswith('sk-ant-') and len(api_key) >= 20
        
        # Generic validation for unknown providers
        return len(api_key) >= 20 and api_key.replace('-', '').replace('_', '').isalnum()
    
    def validate_code_content(self, code: str, language: LanguageType) -> ValidationResult:
        """Validate code content for security issues.
        
        Args:
            code: Code content to validate
            language: Programming language
            
        Returns:
            ValidationResult with validation status
        """
        errors = []
        warnings = []
        
        # Basic validation
        basic_result = self.validate_input(code, "code")
        if not basic_result.valid:
            return basic_result
        
        # Language-specific validation
        if language == LanguageType.PYTHON:
            python_errors, python_warnings = self._validate_python_code(code)
            errors.extend(python_errors)
            warnings.extend(python_warnings)
        
        elif language in [LanguageType.JAVASCRIPT, LanguageType.TYPESCRIPT]:
            js_errors, js_warnings = self._validate_javascript_code(code)
            errors.extend(js_errors)
            warnings.extend(js_warnings)
        
        # Generic dangerous patterns
        dangerous_found = self._detect_dangerous_patterns(code)
        if dangerous_found:
            warnings.extend([f"Potentially dangerous pattern: {pattern}" for pattern in dangerous_found])
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            valid=is_valid,
            errors=errors,
            warnings=warnings,
            sanitized_input=code if is_valid else None
        )
    
    def _detect_dangerous_patterns(self, text: str) -> List[str]:
        """Detect dangerous patterns in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of detected dangerous patterns
        """
        found_patterns = []
        
        for i, pattern in enumerate(self.compiled_patterns):
            matches = pattern.findall(text)
            if matches:
                found_patterns.append(f"Pattern {i+1}: {self.dangerous_patterns[i]}")
        
        return found_patterns
    
    def _validate_by_type(self, input_str: str, input_type: str) -> Tuple[List[str], List[str], str]:
        """Validate input based on specific type.
        
        Args:
            input_str: Input string to validate
            input_type: Type of input
            
        Returns:
            Tuple of (errors, warnings, sanitized_input)
        """
        errors = []
        warnings = []
        sanitized = input_str
        
        if input_type == "filename":
            if not self.allowed_chars['filename'].match(input_str):
                errors.append("Invalid characters in filename")
            if len(input_str) > 255:
                errors.append("Filename too long")
        
        elif input_type == "variable_name":
            if not self.allowed_chars['variable_name'].match(input_str):
                errors.append("Invalid variable name format")
        
        elif input_type == "code":
            # Additional code-specific validation
            if len(input_str.split('\n')) > 10000:
                warnings.append("Very large code file")
            
            # Check for potential obfuscation
            if self._detect_obfuscation(input_str):
                warnings.append("Potentially obfuscated code detected")
        
        elif input_type == "description":
            # Validate description text
            if len(input_str) > 5000:
                warnings.append("Very long description")
        
        return errors, warnings, sanitized
    
    def _sanitize_input(self, input_str: str, input_type: str) -> str:
        """Sanitize input string.
        
        Args:
            input_str: String to sanitize
            input_type: Type of input
            
        Returns:
            Sanitized string
        """
        # Remove null bytes
        sanitized = input_str.replace('\x00', '')
        
        # Normalize line endings
        sanitized = sanitized.replace('\r\n', '\n').replace('\r', '\n')
        
        # Limit line length for display
        if input_type in ["description", "message"]:
            lines = sanitized.split('\n')
            sanitized_lines = []
            for line in lines:
                if len(line) > 1000:
                    sanitized_lines.append(line[:1000] + '...')
                else:
                    sanitized_lines.append(line)
            sanitized = '\n'.join(sanitized_lines)
        
        return sanitized
    
    def _validate_python_code(self, code: str) -> Tuple[List[str], List[str]]:
        """Validate Python-specific code patterns.
        
        Args:
            code: Python code to validate
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        # Dangerous Python patterns
        dangerous_imports = [
            'os.system', 'subprocess.call', 'subprocess.run', 'subprocess.Popen',
            'eval', 'exec', '__import__', 'compile', 'open',
            'pickle.loads', 'marshal.loads', 'shelve.open'
        ]
        
        for pattern in dangerous_imports:
            if pattern in code:
                warnings.append(f"Potentially dangerous Python function: {pattern}")
        
        # Check for dynamic code execution
        dynamic_patterns = ['eval(', 'exec(', 'compile(']
        for pattern in dynamic_patterns:
            if pattern in code:
                errors.append(f"Dynamic code execution detected: {pattern}")
        
        return errors, warnings
    
    def _validate_javascript_code(self, code: str) -> Tuple[List[str], List[str]]:
        """Validate JavaScript-specific code patterns.
        
        Args:
            code: JavaScript code to validate
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        # Dangerous JavaScript patterns
        dangerous_functions = [
            'eval(', 'Function(', 'setTimeout(', 'setInterval(',
            'document.write(', 'innerHTML', 'outerHTML'
        ]
        
        for pattern in dangerous_functions:
            if pattern in code:
                warnings.append(f"Potentially dangerous JavaScript function: {pattern}")
        
        # XSS patterns
        xss_patterns = ['<script', 'javascript:', 'onclick=', 'onerror=']
        for pattern in xss_patterns:
            if pattern.lower() in code.lower():
                errors.append(f"Potential XSS pattern detected: {pattern}")
        
        return errors, warnings
    
    def _detect_obfuscation(self, code: str) -> bool:
        """Detect potentially obfuscated code.
        
        Args:
            code: Code to analyze
            
        Returns:
            True if obfuscation is detected
        """
        # Check for excessive string concatenation
        if code.count('+') > len(code) // 50:
            return True
        
        # Check for excessive character encoding
        if code.count('\\x') > 10 or code.count('\\u') > 10:
            return True
        
        # Check for very short variable names in excess
        short_vars = re.findall(r'\b[a-zA-Z]\b', code)
        if len(short_vars) > len(code) // 100:
            return True
        
        return False


class SecureHasher:
    """Secure hashing utilities."""
    
    @staticmethod
    def hash_content(content: str, algorithm: str = "sha256") -> str:
        """Create secure hash of content.
        
        Args:
            content: Content to hash
            algorithm: Hash algorithm to use
            
        Returns:
            Hexadecimal hash string
        """
        hasher = hashlib.new(algorithm)
        hasher.update(content.encode('utf-8'))
        return hasher.hexdigest()
    
    @staticmethod
    def verify_hash(content: str, expected_hash: str, algorithm: str = "sha256") -> bool:
        """Verify content against expected hash.
        
        Args:
            content: Content to verify
            expected_hash: Expected hash value
            algorithm: Hash algorithm used
            
        Returns:
            True if hash matches
        """
        computed_hash = SecureHasher.hash_content(content, algorithm)
        return hmac.compare_digest(computed_hash, expected_hash)
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate secure random token.
        
        Args:
            length: Token length in bytes
            
        Returns:
            Secure random token as hex string
        """
        return secrets.token_hex(length)


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, max_requests: int = 100, time_window: int = 3600):
        """Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests per time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, List[float]] = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed for identifier.
        
        Args:
            identifier: Unique identifier (e.g., IP, user ID)
            
        Returns:
            True if request is allowed
        """
        import time
        
        current_time = time.time()
        
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Remove old requests outside time window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if current_time - req_time < self.time_window
        ]
        
        # Check if under limit
        if len(self.requests[identifier]) < self.max_requests:
            self.requests[identifier].append(current_time)
            return True
        
        return False
    
    def get_remaining_requests(self, identifier: str) -> int:
        """Get remaining requests for identifier.
        
        Args:
            identifier: Unique identifier
            
        Returns:
            Number of remaining requests
        """
        if identifier not in self.requests:
            return self.max_requests
        
        import time
        current_time = time.time()
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if current_time - req_time < self.time_window
        ]
        
        return max(0, self.max_requests - len(self.requests[identifier]))


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace dangerous characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove null bytes and control characters
    sanitized = ''.join(char for char in sanitized if ord(char) >= 32)
    
    # Limit length
    if len(sanitized) > 255:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        sanitized = name[:255-len(ext)-1] + '.' + ext if ext else name[:255]
    
    # Ensure not empty
    if not sanitized or sanitized == '.':
        sanitized = 'untitled'
    
    return sanitized


def escape_shell_argument(arg: str) -> str:
    """Escape shell argument for safe command execution.
    
    Args:
        arg: Argument to escape
        
    Returns:
        Escaped argument
    """
    # Simple escaping - enclose in single quotes and escape any single quotes
    return "'" + arg.replace("'", "'\"'\"'") + "'"
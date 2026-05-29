"""Security utilities — input sanitization and prompt injection defense."""
import re
from typing import Callable, Dict, List, Optional


class PromptInjectionError(Exception):
    """Raised when a potential prompt injection is detected."""

    def __init__(self, message: str, detected_patterns: List[str] = None):
        self.detected_patterns = detected_patterns or []
        super().__init__(message)


# Common prompt injection patterns
_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(all\s+)?above\s+instructions",
    r"disregard\s+(all\s+)?previous",
    r"forget\s+(all\s+)?previous",
    r"override\s+(all\s+)?instructions",
    r"new\s+instructions?\s*:",
    r"system\s*prompt\s*:",
    r"you\s+are\s+now\s+",
    r"pretend\s+you\s+are",
    r"act\s+as\s+if\s+you",
    r"from\s+now\s+on\s*,?\s*(you|ignore|forget)",
    r"\[system\]",
    r"\[INST\]",
    r"<<\s*SYS\s*>>",
    r"<\|im_start\|>",
    r"###\s*(system|instruction)",
]

_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]


def detect_injection(text: str, extra_patterns: List[str] = None) -> List[str]:
    """Scan text for potential prompt injection patterns.

    Returns a list of matched pattern descriptions (empty if clean).
    """
    matches = []
    all_patterns = list(_COMPILED_PATTERNS)

    if extra_patterns:
        all_patterns.extend(re.compile(p, re.IGNORECASE) for p in extra_patterns)

    for pattern in all_patterns:
        if pattern.search(text):
            matches.append(pattern.pattern)

    return matches


def sanitize_input(
    text: str,
    max_length: int = 10000,
    strip_control_chars: bool = True,
    strip_html: bool = True,
    check_injection: bool = True,
    on_injection: str = "raise",
) -> str:
    """Sanitize user input before passing to an LLM.

    Args:
        text: Raw user input
        max_length: Maximum allowed length (truncates if exceeded)
        strip_control_chars: Remove non-printable control characters
        strip_html: Remove HTML/XML tags
        check_injection: Scan for prompt injection attempts
        on_injection: "raise" to throw error, "warn" to strip and continue, "log" to pass through with warning

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    result = text

    if strip_control_chars:
        result = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", result)

    if strip_html:
        result = re.sub(r"<[^>]+>", "", result)

    if max_length and len(result) > max_length:
        result = result[:max_length]

    if check_injection:
        detected = detect_injection(result)
        if detected:
            if on_injection == "raise":
                raise PromptInjectionError(
                    f"Potential prompt injection detected: {len(detected)} suspicious pattern(s)",
                    detected_patterns=detected,
                )
            elif on_injection == "warn":
                for pattern in _COMPILED_PATTERNS:
                    result = pattern.sub("[REDACTED]", result)

    return result


class SecurePromptTemplate:
    """A prompt template that sanitizes all inputs before formatting.

    Wraps PromptTemplate and applies sanitization to every variable.
    """

    def __init__(
        self,
        template,
        max_input_length: int = 5000,
        check_injection: bool = True,
        on_injection: str = "raise",
    ):
        self.template = template
        self.max_input_length = max_input_length
        self.check_injection = check_injection
        self.on_injection = on_injection

    def format(self, **kwargs) -> str:
        sanitized = {}
        for key, value in kwargs.items():
            if isinstance(value, str):
                sanitized[key] = sanitize_input(
                    value,
                    max_length=self.max_input_length,
                    check_injection=self.check_injection,
                    on_injection=self.on_injection,
                )
            else:
                sanitized[key] = value
        return self.template.format(**sanitized)

    @property
    def input_variables(self):
        return self.template.input_variables

    def __repr__(self) -> str:
        return f"SecurePromptTemplate(template={self.template!r})"


class InputSanitizer:
    """Configurable sanitizer that can be applied to chains.

    Usage:
        sanitizer = InputSanitizer(max_length=5000, check_injection=True)
        safe_chain = sanitizer.wrap(chain)
    """

    def __init__(
        self,
        max_length: int = 10000,
        strip_control_chars: bool = True,
        strip_html: bool = True,
        check_injection: bool = True,
        on_injection: str = "raise",
        allowed_patterns: List[str] = None,
        blocked_patterns: List[str] = None,
    ):
        self.max_length = max_length
        self.strip_control_chars = strip_control_chars
        self.strip_html = strip_html
        self.check_injection = check_injection
        self.on_injection = on_injection
        self.allowed_patterns = allowed_patterns or []
        self.blocked_patterns = blocked_patterns or []

    def sanitize(self, text: str) -> str:
        return sanitize_input(
            text,
            max_length=self.max_length,
            strip_control_chars=self.strip_control_chars,
            strip_html=self.strip_html,
            check_injection=self.check_injection,
            on_injection=self.on_injection,
        )

    def sanitize_dict(self, inputs: Dict) -> Dict:
        """Sanitize all string values in a dict."""
        result = {}
        for key, value in inputs.items():
            if isinstance(value, str):
                result[key] = self.sanitize(value)
            else:
                result[key] = value
        return result

    def wrap(self, chain):
        """Wrap a chain to sanitize inputs before execution."""
        from functools import wraps

        original_invoke = chain.invoke

        @wraps(original_invoke)
        def safe_invoke(inputs, **kwargs):
            if isinstance(inputs, dict):
                inputs = self.sanitize_dict(inputs)
            elif isinstance(inputs, str):
                inputs = self.sanitize(inputs)
            return original_invoke(inputs, **kwargs)

        chain.invoke = safe_invoke
        return chain


def redact_sensitive(text: str, patterns: Dict[str, str] = None) -> str:
    """Redact sensitive information from text (e.g., before logging).

    Default patterns: emails, phone numbers, SSN-like patterns, API keys.
    """
    default_patterns = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "api_key": r"\b[A-Za-z0-9]{32,}\b",
        "bearer_token": r"Bearer\s+[A-Za-z0-9\-._~+/]+=*",
    }

    all_patterns = {**default_patterns, **(patterns or {})}
    result = text

    for name, pattern in all_patterns.items():
        result = re.sub(pattern, f"[REDACTED_{name.upper()}]", result)

    return result

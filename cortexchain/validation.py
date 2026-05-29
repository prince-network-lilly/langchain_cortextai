"""Input validation utilities for chains and tools."""
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set


class ValidationError(Exception):
    """Raised when input validation fails."""

    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"Validation failed: {'; '.join(errors)}")


def validate_inputs(
    required: Optional[List[str]] = None,
    types: Optional[Dict[str, type]] = None,
    validators: Optional[Dict[str, Callable[[Any], bool]]] = None,
    max_length: Optional[Dict[str, int]] = None,
):
    """Decorator that validates chain/function inputs before execution.

    Usage:
        @validate_inputs(
            required=["query", "context"],
            types={"query": str, "k": int},
            max_length={"query": 5000},
            validators={"k": lambda v: v > 0}
        )
        def my_chain_invoke(self, inputs):
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            inputs = _extract_inputs(args, kwargs)
            if inputs is not None:
                errors = _validate(inputs, required, types, validators, max_length)
                if errors:
                    raise ValidationError(errors)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_not_empty(*keys: str):
    """Decorator ensuring specified keys are non-empty strings."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            inputs = _extract_inputs(args, kwargs)
            if inputs is not None:
                errors = []
                for key in keys:
                    val = inputs.get(key)
                    if val is None or (isinstance(val, str) and not val.strip()):
                        errors.append(f"'{key}' must be a non-empty string")
                if errors:
                    raise ValidationError(errors)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_schema(schema: Dict[str, type]):
    """Decorator validating that inputs match a type schema."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            inputs = _extract_inputs(args, kwargs)
            if inputs is not None:
                errors = []
                for key, expected_type in schema.items():
                    if key in inputs and not isinstance(inputs[key], expected_type):
                        errors.append(
                            f"'{key}' expected {expected_type.__name__}, got {type(inputs[key]).__name__}"
                        )
                if errors:
                    raise ValidationError(errors)
            return func(*args, **kwargs)

        return wrapper

    return decorator


class InputValidator:
    """Composable validator that can be attached to chains.

    Usage:
        validator = InputValidator()
        validator.require("query", "context")
        validator.type_check({"query": str, "k": int})
        validator.add_rule("k", lambda v: v > 0, "k must be positive")

        validated_chain = validator.wrap(my_chain)
    """

    def __init__(self):
        self._required: Set[str] = set()
        self._types: Dict[str, type] = {}
        self._rules: List[tuple] = []
        self._max_lengths: Dict[str, int] = {}

    def require(self, *keys: str) -> "InputValidator":
        self._required.update(keys)
        return self

    def type_check(self, schema: Dict[str, type]) -> "InputValidator":
        self._types.update(schema)
        return self

    def add_rule(self, key: str, check: Callable[[Any], bool], message: str) -> "InputValidator":
        self._rules.append((key, check, message))
        return self

    def max_length(self, key: str, length: int) -> "InputValidator":
        self._max_lengths[key] = length
        return self

    def validate(self, inputs: Dict) -> List[str]:
        return _validate(inputs, list(self._required), self._types, None, self._max_lengths) + self._check_rules(inputs)

    def _check_rules(self, inputs: Dict) -> List[str]:
        errors = []
        for key, check, message in self._rules:
            if key in inputs:
                try:
                    if not check(inputs[key]):
                        errors.append(message)
                except Exception:
                    errors.append(message)
        return errors

    def wrap(self, chain):
        """Wrap a chain so invoke() validates inputs first."""
        original_invoke = chain.invoke

        @wraps(original_invoke)
        def validated_invoke(inputs, **kwargs):
            errors = self.validate(inputs)
            if errors:
                raise ValidationError(errors)
            return original_invoke(inputs, **kwargs)

        chain.invoke = validated_invoke
        return chain


def _extract_inputs(args, kwargs) -> Optional[Dict]:
    """Extract the inputs dict from function args (handles self.invoke(inputs) pattern)."""
    if kwargs.get("inputs"):
        return kwargs["inputs"]
    for arg in args:
        if isinstance(arg, dict):
            return arg
    return None


def _validate(
    inputs: Dict,
    required: Optional[List[str]],
    types: Optional[Dict[str, type]],
    validators: Optional[Dict[str, Callable]],
    max_length: Optional[Dict[str, int]],
) -> List[str]:
    errors = []

    if required:
        for key in required:
            if key not in inputs:
                errors.append(f"Missing required input: '{key}'")

    if types:
        for key, expected in types.items():
            if key in inputs and not isinstance(inputs[key], expected):
                errors.append(f"'{key}' expected {expected.__name__}, got {type(inputs[key]).__name__}")

    if validators:
        for key, fn in validators.items():
            if key in inputs:
                try:
                    if not fn(inputs[key]):
                        errors.append(f"Validation failed for '{key}'")
                except Exception as e:
                    errors.append(f"Validator error for '{key}': {e}")

    if max_length:
        for key, max_len in max_length.items():
            if key in inputs and hasattr(inputs[key], "__len__") and len(inputs[key]) > max_len:
                errors.append(f"'{key}' exceeds max length {max_len} (got {len(inputs[key])})")

    return errors

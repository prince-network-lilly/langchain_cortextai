"""Tests for cortexchain.validation"""
import pytest
from cortexchain.validation import (
    validate_inputs, validate_not_empty, validate_schema,
    InputValidator, ValidationError,
)


class TestValidateInputsDecorator:
    def test_required_fields_pass(self):
        @validate_inputs(required=["name"])
        def fn(inputs):
            return inputs

        result = fn({"name": "Alice"})
        assert result["name"] == "Alice"

    def test_required_fields_fail(self):
        @validate_inputs(required=["name", "age"])
        def fn(inputs):
            return inputs

        with pytest.raises(ValidationError) as exc_info:
            fn({"name": "Alice"})
        assert "age" in str(exc_info.value)

    def test_type_check_pass(self):
        @validate_inputs(types={"count": int})
        def fn(inputs):
            return inputs

        assert fn({"count": 5}) == {"count": 5}

    def test_type_check_fail(self):
        @validate_inputs(types={"count": int})
        def fn(inputs):
            return inputs

        with pytest.raises(ValidationError):
            fn({"count": "not_an_int"})

    def test_max_length(self):
        @validate_inputs(max_length={"query": 10})
        def fn(inputs):
            return inputs

        with pytest.raises(ValidationError) as exc_info:
            fn({"query": "a" * 20})
        assert "max length" in str(exc_info.value)

    def test_custom_validator(self):
        @validate_inputs(validators={"k": lambda v: v > 0})
        def fn(inputs):
            return inputs

        assert fn({"k": 5}) == {"k": 5}
        with pytest.raises(ValidationError):
            fn({"k": -1})


class TestValidateNotEmpty:
    def test_passes_with_content(self):
        @validate_not_empty("query")
        def fn(inputs):
            return inputs

        assert fn({"query": "hello"}) == {"query": "hello"}

    def test_fails_on_empty(self):
        @validate_not_empty("query")
        def fn(inputs):
            return inputs

        with pytest.raises(ValidationError):
            fn({"query": "   "})

    def test_fails_on_none(self):
        @validate_not_empty("query")
        def fn(inputs):
            return inputs

        with pytest.raises(ValidationError):
            fn({"query": None})


class TestValidateSchema:
    def test_passes(self):
        @validate_schema({"name": str, "count": int})
        def fn(inputs):
            return inputs

        assert fn({"name": "x", "count": 3}) == {"name": "x", "count": 3}

    def test_fails(self):
        @validate_schema({"name": str})
        def fn(inputs):
            return inputs

        with pytest.raises(ValidationError):
            fn({"name": 123})


class TestInputValidator:
    def test_require(self):
        v = InputValidator().require("a", "b")
        errors = v.validate({"a": 1})
        assert any("b" in e for e in errors)

    def test_type_check(self):
        v = InputValidator().type_check({"x": int})
        errors = v.validate({"x": "wrong"})
        assert len(errors) == 1

    def test_add_rule(self):
        v = InputValidator().add_rule("k", lambda val: val > 0, "k must be positive")
        assert v.validate({"k": 5}) == []
        errors = v.validate({"k": -1})
        assert "k must be positive" in errors

    def test_wrap_chain(self):
        class FakeChain:
            def invoke(self, inputs):
                return {"result": inputs["x"] * 2}

        chain = FakeChain()
        v = InputValidator().require("x").type_check({"x": int})
        v.wrap(chain)

        assert chain.invoke({"x": 3}) == {"result": 6}
        with pytest.raises(ValidationError):
            chain.invoke({"y": 3})

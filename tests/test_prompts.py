"""Tests for cortexchain.prompts.templates"""

from cortexchain.prompts.templates import PromptTemplate


def test_from_template():
    pt = PromptTemplate.from_template("Hello {name}, you are {age} years old.")
    assert pt.input_variables == ["name", "age"]


def test_format():
    pt = PromptTemplate.from_template("Say {greeting} to {person}")
    result = pt.format(greeting="hello", person="Alice")
    assert result == "Say hello to Alice"


def test_duplicate_variables():
    pt = PromptTemplate.from_template("{x} and {x} and {y}")
    assert pt.input_variables == ["x", "y"]


def test_no_variables():
    pt = PromptTemplate.from_template("No variables here.")
    assert pt.input_variables == []
    assert pt.format() == "No variables here."


def test_pipe_operator():
    """Pipe syntax should create an LLMChain (can't fully test without LLM)."""
    pt = PromptTemplate.from_template("Test {input}")
    # Just verify it has __or__ method
    assert hasattr(pt, "__or__")

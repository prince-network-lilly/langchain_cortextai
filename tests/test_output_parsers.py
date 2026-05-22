"""Tests for cortexchain.output_parsers"""
import pytest
from cortexchain.output_parsers.json_parser import JSONOutputParser
from cortexchain.output_parsers.list_parser import ListOutputParser
from cortexchain.output_parsers.regex_parser import RegexParser


class TestJSONOutputParser:
    def test_parse_raw_json(self):
        parser = JSONOutputParser()
        result = parser.parse('{"name": "Alice", "age": 30}')
        assert result == {"name": "Alice", "age": 30}

    def test_parse_json_in_code_block(self):
        parser = JSONOutputParser()
        text = 'Here is the result:\n```json\n{"key": "value"}\n```'
        result = parser.parse(text)
        assert result == {"key": "value"}

    def test_parse_with_schema_validation(self):
        parser = JSONOutputParser(schema={"name": "string", "age": "int"})
        result = parser.parse('{"name": "Bob", "age": 25}')
        assert result["name"] == "Bob"

    def test_parse_missing_schema_key_raises(self):
        parser = JSONOutputParser(schema={"name": "string", "email": "string"})
        with pytest.raises(ValueError, match="Missing required key"):
            parser.parse('{"name": "Bob"}')

    def test_parse_invalid_json_raises(self):
        parser = JSONOutputParser()
        with pytest.raises(ValueError, match="Failed to parse JSON"):
            parser.parse("This is not JSON at all")

    def test_format_instructions(self):
        parser = JSONOutputParser(schema={"name": "string"})
        instructions = parser.get_format_instructions()
        assert "JSON" in instructions


class TestListOutputParser:
    def test_parse_numbered_list(self):
        parser = ListOutputParser()
        text = "1. Apple\n2. Banana\n3. Cherry"
        result = parser.parse(text)
        assert result == ["Apple", "Banana", "Cherry"]

    def test_parse_bullet_list(self):
        parser = ListOutputParser()
        text = "- First\n- Second\n- Third"
        result = parser.parse(text)
        assert result == ["First", "Second", "Third"]

    def test_parse_with_separator(self):
        parser = ListOutputParser(separator=",")
        result = parser.parse("red, green, blue")
        assert result == ["red", "green", "blue"]

    def test_parse_fallback_newlines(self):
        parser = ListOutputParser()
        text = "line one\nline two\nline three"
        result = parser.parse(text)
        assert len(result) == 3


class TestRegexParser:
    def test_parse_named_groups(self):
        parser = RegexParser(r"Name: (?P<name>\w+), Age: (?P<age>\d+)")
        result = parser.parse("Name: Alice, Age: 30")
        assert result == {"name": "Alice", "age": "30"}

    def test_parse_with_output_keys(self):
        parser = RegexParser(r"(\w+)\s*:\s*(\d+)", output_keys=["name", "value"])
        result = parser.parse("score: 95")
        assert result == {"name": "score", "value": "95"}

    def test_parse_no_match_raises(self):
        parser = RegexParser(r"IMPOSSIBLE_PATTERN_XYZ")
        with pytest.raises(ValueError, match="Could not parse"):
            parser.parse("normal text here")

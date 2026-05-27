"""Tests for cortexchain.tools"""

from cortexchain.tools.base import BaseTool, FunctionTool, tool


class TestToolDecorator:
    def test_decorator_no_args(self):
        @tool
        def my_tool(x: str) -> str:
            """Does something useful."""
            return f"result: {x}"

        assert my_tool.name == "my_tool"
        assert my_tool.description == "Does something useful."
        assert my_tool.run("hello") == "result: hello"

    def test_decorator_with_args(self):
        @tool(name="custom_name", description="Custom desc")
        def another(x: str) -> str:
            return x.upper()

        assert another.name == "custom_name"
        assert another.description == "Custom desc"
        assert another.run("hello") == "HELLO"

    def test_tool_callable(self):
        @tool
        def add(x: str) -> str:
            """Adds one."""
            return str(int(x) + 1)

        assert add("5") == "6"

    def test_tool_error_handling(self):
        @tool
        def bad_tool(x: str) -> str:
            """Always fails."""
            raise ValueError("intentional error")

        result = bad_tool.run("test")
        assert "Tool error" in result
        assert "intentional error" in result


class TestFunctionTool:
    def test_basic(self):
        ft = FunctionTool(func=lambda x: x * 2, name="doubler", description="Doubles input")
        assert ft.name == "doubler"
        assert ft.run("3") == "33"

    def test_repr(self):
        ft = FunctionTool(func=lambda x: x, name="test", description="Test tool")
        assert "test" in repr(ft)


class TestBaseTool:
    def test_subclass(self):
        class MyTool(BaseTool):
            name = "my_tool"
            description = "A custom tool"

            def run(self, tool_input: str) -> str:
                return f"processed: {tool_input}"

        t = MyTool()
        assert t.name == "my_tool"
        assert t("hello") == "processed: hello"

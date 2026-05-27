"""Tests for cortexchain.schema"""

from cortexchain.schema import LLMResult, Message, Document, GraphState, AgentAction, AgentFinish


def test_llm_result_str():
    r = LLMResult(message="Hello world")
    assert str(r) == "Hello world"


def test_message_str():
    m = Message(role="human", content="Hi")
    assert "human" in str(m)
    assert "Hi" in str(m)


def test_document():
    doc = Document(page_content="Test content", metadata={"source": "test.txt"})
    assert str(doc) == "Test content"
    assert len(doc) == len("Test content")
    assert doc.metadata["source"] == "test.txt"


def test_graph_state():
    state = GraphState()
    state["key"] = "value"
    assert state["key"] == "value"
    assert state.get("missing", "default") == "default"

    state.update({"a": 1, "b": 2})
    assert state["a"] == 1

    copy = state.copy()
    copy["new"] = True
    assert "new" not in state.data


def test_agent_action():
    action = AgentAction(tool="calc", tool_input="2+2", log="thinking...")
    assert action.tool == "calc"


def test_agent_finish():
    finish = AgentFinish(output="The answer is 4", log="done")
    assert finish.output == "The answer is 4"

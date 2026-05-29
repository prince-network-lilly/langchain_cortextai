"""Tests for cortexchain.graph.state_graph"""
from cortexchain.graph.state_graph import StateGraph, CompiledGraph, END
from cortexchain.graph.checkpoint import MemoryCheckpointer


def test_simple_linear_graph():
    graph = StateGraph()
    graph.add_node("step1", lambda s: {**s, "step1": True})
    graph.add_node("step2", lambda s: {**s, "step2": True})
    graph.add_edge("step1", "step2")
    graph.add_edge("step2", END)
    graph.set_entry_point("step1")

    app = graph.compile()
    result = app.invoke({"input": "test"})
    assert result["step1"] is True
    assert result["step2"] is True


def test_conditional_edges():
    def router(state):
        return "positive" if state.get("sentiment") == "good" else "negative"

    graph = StateGraph()
    graph.add_node("analyze", lambda s: {**s, "analyzed": True})
    graph.add_node("positive", lambda s: {**s, "response": "Great!"})
    graph.add_node("negative", lambda s: {**s, "response": "Sorry to hear."})

    graph.add_conditional_edges("analyze", router, {"positive": "positive", "negative": "negative"})
    graph.add_edge("positive", END)
    graph.add_edge("negative", END)
    graph.set_entry_point("analyze")

    app = graph.compile()

    result = app.invoke({"sentiment": "good"})
    assert result["response"] == "Great!"

    result = app.invoke({"sentiment": "bad"})
    assert result["response"] == "Sorry to hear."


def test_graph_with_checkpointer():
    graph = StateGraph()
    graph.add_node("increment", lambda s: {**s, "count": s.get("count", 0) + 1})
    graph.add_edge("increment", END)
    graph.set_entry_point("increment")

    checkpointer = MemoryCheckpointer()
    app = graph.compile(checkpointer=checkpointer)
    app.invoke({"input": "test"}, config={"thread_id": "t1"})

    saved = checkpointer.load("t1")
    assert saved is not None
    assert saved["state"]["count"] == 1


def test_graph_stream():
    graph = StateGraph()
    graph.add_node("a", lambda s: {**s, "a_done": True})
    graph.add_node("b", lambda s: {**s, "b_done": True})
    graph.add_edge("a", "b")
    graph.add_edge("b", END)
    graph.set_entry_point("a")

    app = graph.compile()
    events = list(app.stream({"input": "go"}))
    assert len(events) == 2
    assert events[0]["node"] == "a"
    assert events[1]["node"] == "b"


def test_max_steps_guard():
    graph = StateGraph()
    graph.add_node("loop", lambda s: {**s, "count": s.get("count", 0) + 1})
    graph.add_edge("loop", "loop")  # infinite loop
    graph.set_entry_point("loop")

    app = graph.compile()
    result = app.invoke({}, max_steps=5)
    assert result["count"] == 5
    assert result["__steps__"] == 5

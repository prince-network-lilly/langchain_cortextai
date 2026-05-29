"""Tests for cortexchain.memory.buffer"""
from cortexchain.memory.buffer import ConversationBufferMemory, ConversationWindowMemory


def test_buffer_memory_add_and_retrieve():
    mem = ConversationBufferMemory()
    mem.add_user_message("Hello")
    mem.add_ai_message("Hi there!")
    assert len(mem) == 2
    history = mem.get_history_string()
    assert "Human: Hello" in history
    assert "AI: Hi there!" in history


def test_buffer_memory_clear():
    mem = ConversationBufferMemory()
    mem.add_user_message("test")
    mem.clear()
    assert len(mem) == 0
    assert mem.get_history_string() == ""


def test_buffer_memory_custom_prefix():
    mem = ConversationBufferMemory(human_prefix="User", ai_prefix="Bot")
    mem.add_user_message("Hey")
    mem.add_ai_message("Hello!")
    history = mem.get_history_string()
    assert "User: Hey" in history
    assert "Bot: Hello!" in history


def test_window_memory_respects_k():
    mem = ConversationWindowMemory(k=2)
    mem.add_user_message("msg1")
    mem.add_ai_message("resp1")
    mem.add_user_message("msg2")
    mem.add_ai_message("resp2")
    mem.add_user_message("msg3")
    mem.add_ai_message("resp3")

    history = mem.get_history_string()
    # k=2 means last 4 messages (2 pairs)
    assert "msg1" not in history
    assert "msg2" in history
    assert "msg3" in history


def test_window_memory_less_than_k():
    mem = ConversationWindowMemory(k=10)
    mem.add_user_message("only one")
    mem.add_ai_message("response")
    history = mem.get_history_string()
    assert "only one" in history

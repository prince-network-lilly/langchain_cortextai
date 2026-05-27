"""Tests for cortexchain.async_support"""

import asyncio
import pytest
from unittest.mock import patch, MagicMock
from cortexchain.async_support import AsyncCortexLLM, AsyncLLMChain, AsyncSequentialChain
from cortexchain.schema import LLMResult
from cortexchain.prompts.templates import PromptTemplate


@pytest.fixture
def mock_llm_result():
    return LLMResult(message="Hello from Cortex")


class TestAsyncCortexLLM:
    def test_init(self):
        with patch("cortexchain.llm.cortex.LIGHTClient"):
            llm = AsyncCortexLLM(agent_name="test-agent")
            assert llm.agent_name == "test-agent"

    @pytest.mark.asyncio
    async def test_ainvoke(self, mock_llm_result):
        with patch("cortexchain.llm.cortex.LIGHTClient") as mock_client:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"message": "Hello from Cortex"}
            mock_client.return_value.post.return_value = mock_resp

            llm = AsyncCortexLLM(agent_name="test-agent")
            result = await llm.ainvoke("Hello")
            assert result.message == "Hello from Cortex"

    @pytest.mark.asyncio
    async def test_call(self, mock_llm_result):
        with patch("cortexchain.llm.cortex.LIGHTClient") as mock_client:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"message": "Response"}
            mock_client.return_value.post.return_value = mock_resp

            llm = AsyncCortexLLM(agent_name="test-agent")
            text = await llm("Hello")
            assert text == "Response"

    @pytest.mark.asyncio
    async def test_abatch(self):
        with patch("cortexchain.llm.cortex.LIGHTClient") as mock_client:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"message": "batch-response"}
            mock_client.return_value.post.return_value = mock_resp

            llm = AsyncCortexLLM(agent_name="test-agent")
            results = await llm.abatch(["p1", "p2", "p3"])
            assert len(results) == 3
            assert all(r.message == "batch-response" for r in results)


class TestAsyncLLMChain:
    @pytest.mark.asyncio
    async def test_ainvoke(self):
        with patch("cortexchain.llm.cortex.LIGHTClient") as mock_client:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"message": "chain result"}
            mock_client.return_value.post.return_value = mock_resp

            llm = AsyncCortexLLM(agent_name="test")
            prompt = PromptTemplate(template="Say {word}")
            chain = AsyncLLMChain(llm=llm, prompt=prompt)

            result = await chain.ainvoke({"word": "hello"})
            assert result["text"] == "chain result"

    @pytest.mark.asyncio
    async def test_arun(self):
        with patch("cortexchain.llm.cortex.LIGHTClient") as mock_client:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"message": "run result"}
            mock_client.return_value.post.return_value = mock_resp

            llm = AsyncCortexLLM(agent_name="test")
            prompt = PromptTemplate(template="Translate {text}")
            chain = AsyncLLMChain(llm=llm, prompt=prompt)

            text = await chain.arun(text="hello")
            assert text == "run result"


class TestAsyncSequentialChain:
    @pytest.mark.asyncio
    async def test_sequential(self):
        class FakeAsyncChain:
            def __init__(self, suffix):
                self.suffix = suffix

            async def ainvoke(self, inputs):
                return {**inputs, f"step_{self.suffix}": True}

        chain = AsyncSequentialChain(chains=[FakeAsyncChain("a"), FakeAsyncChain("b")])
        result = await chain.ainvoke({"input": "test"})
        assert result["step_a"] is True
        assert result["step_b"] is True

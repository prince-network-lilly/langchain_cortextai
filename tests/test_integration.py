"""Integration tests — test full chains end-to-end with mocked Cortex API."""
import pytest
from unittest.mock import patch, MagicMock, call
from cortexchain.llm.cortex import CortexLLM
from cortexchain.chains.llm_chain import LLMChain
from cortexchain.chains.conversation import ConversationChain
from cortexchain.chains.sequential import SimpleSequentialChain
from cortexchain.chains.structured_output import StructuredOutputChain
from cortexchain.prompts.templates import PromptTemplate
from cortexchain.memory.buffer import ConversationBufferMemory
from cortexchain.schema import LLMResult


class TestLLMChainIntegration:
    def test_prompt_to_llm_full_flow(self, cortex_llm, mock_light_client, mock_cortex_response):
        prompt = PromptTemplate(template="Summarize: {text}")
        chain = LLMChain(llm=cortex_llm, prompt=prompt)

        result = chain.invoke({"text": "Python is great for data science."})

        assert result["text"] == mock_cortex_response["message"]
        mock_light_client.post.assert_called_once()
        posted_data = mock_light_client.post.call_args
        assert "Summarize: Python is great for data science." in str(posted_data)

    def test_chain_run_shorthand(self, cortex_llm):
        prompt = PromptTemplate(template="Translate to French: {input}")
        chain = LLMChain(llm=cortex_llm, prompt=prompt)

        result = chain.run(input="Hello world")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_chain_call_with_string(self, cortex_llm):
        prompt = PromptTemplate(template="Explain: {input}")
        chain = LLMChain(llm=cortex_llm, prompt=prompt)

        result = chain("What is MLOps?")
        assert "text" in result


class TestConversationChainIntegration:
    def test_multi_turn_conversation(self, mock_light_client):
        responses = [
            {"message": "Hello! How can I help?"},
            {"message": "Python is a programming language."},
            {"message": "It was created by Guido van Rossum."},
        ]
        mock_light_client.post.return_value.json.side_effect = responses

        llm = CortexLLM(agent_name="chat-agent")
        chain = ConversationChain(llm=llm)

        r1 = chain("Hi there")
        assert "Hello" in r1["text"]

        r2 = chain("What is Python?")
        assert "programming" in r2["text"]

        r3 = chain("Who created it?")
        assert "Guido" in r3["text"]

        assert mock_light_client.post.call_count == 3

    def test_memory_persists_across_turns(self, mock_light_client):
        mock_light_client.post.return_value.json.side_effect = [
            {"message": "I'm fine, thanks!"},
            {"message": "You asked how I am."},
        ]

        llm = CortexLLM(agent_name="chat-agent")
        memory = ConversationBufferMemory()
        chain = ConversationChain(llm=llm, memory=memory)

        chain("How are you?")
        chain("What did I just ask?")

        history = memory.load_memory()
        assert "How are you?" in history
        assert "I'm fine" in history


class TestSequentialChainIntegration:
    def test_two_step_pipeline(self, mock_light_client):
        mock_light_client.post.return_value.json.side_effect = [
            {"message": "Summary: AI is transforming industries."},
            {"message": "Résumé: L'IA transforme les industries."},
        ]

        llm = CortexLLM(agent_name="pipeline-agent")

        summarize = LLMChain(
            llm=llm,
            prompt=PromptTemplate(template="Summarize: {input}"),
            output_key="text",
        )
        translate = LLMChain(
            llm=llm,
            prompt=PromptTemplate(template="Translate to French: {input}"),
            output_key="text",
        )

        pipeline = SimpleSequentialChain(chains=[summarize, translate])
        result = pipeline.invoke({"input": "A long article about AI..."})

        assert "français" in result["text"].lower() or "Résumé" in result["text"]
        assert mock_light_client.post.call_count == 2


class TestStructuredOutputIntegration:
    def test_json_extraction(self, mock_light_client):
        mock_light_client.post.return_value.json.return_value = {
            "message": '```json\n{"name": "Alice", "age": 30}\n```'
        }

        llm = CortexLLM(agent_name="json-agent")
        chain = StructuredOutputChain(
            llm=llm,
            prompt=PromptTemplate(template="Extract info from: {text}"),
            schema={"name": str, "age": int},
        )

        result = chain.invoke({"text": "Alice is 30 years old."})
        assert result["parsed"]["name"] == "Alice"
        assert result["parsed"]["age"] == 30


class TestLLMDirectIntegration:
    def test_invoke_returns_llm_result(self, cortex_llm, mock_cortex_response):
        result = cortex_llm.invoke("Hello")
        assert isinstance(result, LLMResult)
        assert result.message == mock_cortex_response["message"]
        assert result.llm_model == "gpt-4"

    def test_call_returns_string(self, cortex_llm, mock_cortex_response):
        text = cortex_llm("Hello")
        assert isinstance(text, str)
        assert text == mock_cortex_response["message"]

    def test_with_chat_history(self, cortex_llm, mock_light_client):
        cortex_llm.invoke("Follow up", chat_history="Human: Hi\nAI: Hello!")
        posted_data = mock_light_client.post.call_args
        assert "chat_history" in str(posted_data)

    def test_api_url_construction(self, cortex_llm):
        url = cortex_llm._build_url()
        assert "model/ask/test-agent" in url
        assert "default_knowledge" not in url

    def test_api_url_with_knowledge(self, mock_light_client):
        llm = CortexLLM(agent_name="kb-agent", default_knowledge=True)
        url = llm._build_url()
        assert "default_knowledge=true" in url

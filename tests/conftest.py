"""conftest.py — shared test fixtures for cortexchain tests."""
import pytest
from unittest.mock import patch, MagicMock
from cortexchain.schema import LLMResult, Document
from cortexchain.prompts.templates import PromptTemplate


@pytest.fixture
def mock_cortex_response():
    """Standard mock response from Cortex API."""
    return {
        "message": "This is a test response from Cortex AI.",
        "llm_model": "gpt-4",
        "llm_model_display_name": "GPT-4",
        "source_metadata": [],
        "steps": [],
    }


@pytest.fixture
def mock_light_client(mock_cortex_response):
    """Patches LIGHTClient so CortexLLM can be instantiated without network."""
    with patch("cortexchain.llm.cortex.LIGHTClient") as mock_cls:
        mock_instance = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_cortex_response
        mock_instance.post.return_value = mock_resp
        mock_cls.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def cortex_llm(mock_light_client):
    """A CortexLLM instance with mocked network."""
    from cortexchain.llm.cortex import CortexLLM
    return CortexLLM(agent_name="test-agent")


@pytest.fixture
def sample_prompt():
    """A simple prompt template for testing."""
    return PromptTemplate(template="Answer this: {question}")


@pytest.fixture
def sample_documents():
    """A set of test documents."""
    return [
        Document(page_content="Python is a programming language.", metadata={"source": "wiki"}),
        Document(page_content="Machine learning is a subset of AI.", metadata={"source": "textbook"}),
        Document(page_content="Data pipelines move data from A to B.", metadata={"source": "blog"}),
    ]

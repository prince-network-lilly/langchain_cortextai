from typing import Dict, Optional
from cortexchain.chains.llm_chain import LLMChain
from cortexchain.llm.cortex import CortexLLM
from cortexchain.memory.buffer import ConversationBufferMemory
from cortexchain.prompts.templates import PromptTemplate

_DEFAULT_TEMPLATE = (
    "The following is a friendly conversation between a human and an AI assistant.\n\n"
    "Current conversation:\n{chat_history}\nHuman: {input}\nAI:"
)


class ConversationChain(LLMChain):
    """An LLMChain that automatically tracks conversation history with memory."""

    def __init__(
        self,
        llm: CortexLLM,
        memory: Optional[ConversationBufferMemory] = None,
        prompt: Optional[PromptTemplate] = None,
        verbose: bool = False,
    ):
        if prompt is None:
            prompt = PromptTemplate.from_template(_DEFAULT_TEMPLATE)
        super().__init__(llm=llm, prompt=prompt, output_key="response")
        self.memory = memory or ConversationBufferMemory()
        self.verbose = verbose

    def invoke(self, inputs: Dict) -> Dict:
        user_input = inputs.get("input", "")
        history = self.memory.get_history_string()

        if self.verbose:
            print(f"\n[Human]: {user_input}")

        formatted = self.prompt.format(input=user_input, chat_history=history)
        result = self.llm.invoke(formatted)

        self.memory.add_user_message(user_input)
        self.memory.add_ai_message(result.message)

        if self.verbose:
            print(f"[AI]: {result.message}")

        return {"response": result.message, "_result": result}

    def chat(self, message: str) -> str:
        """Convenience method: send a message and get back the AI response string."""
        return self.invoke({"input": message})["response"]

    @property
    def _default_input_key(self) -> str:
        return "input"

    def __repr__(self) -> str:
        return f"ConversationChain(llm={self.llm!r}, memory={self.memory!r})"

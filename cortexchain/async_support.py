"""Async support for CortexLLM — uses asyncio + threading to avoid blocking."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, AsyncIterator

from cortexchain.llm.cortex import CortexLLM
from cortexchain.schema import LLMResult


class AsyncCortexLLM:
    """Async wrapper around CortexLLM.

    Uses a thread pool to run the synchronous LIGHTClient in an async context.
    """

    def __init__(
        self,
        agent_name: str,
        base_url: str = "https://api.cortex.lilly.com",
        default_knowledge: bool = False,
        max_workers: int = 4,
    ):
        self._sync_llm = CortexLLM(
            agent_name=agent_name,
            base_url=base_url,
            default_knowledge=default_knowledge,
        )
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    @property
    def agent_name(self) -> str:
        return self._sync_llm.agent_name

    async def ainvoke(self, prompt: str, chat_history: str = "") -> LLMResult:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self._sync_llm.invoke, prompt, chat_history)

    async def __call__(self, prompt: str, chat_history: str = "") -> str:
        result = await self.ainvoke(prompt, chat_history)
        return result.message

    async def abatch(self, prompts: list, max_concurrency: int = 4) -> list:
        semaphore = asyncio.Semaphore(max_concurrency)

        async def _call(p):
            async with semaphore:
                return await self.ainvoke(p)

        return await asyncio.gather(*[_call(p) for p in prompts])

    def __repr__(self) -> str:
        return f"AsyncCortexLLM(agent_name={self.agent_name!r})"


class AsyncLLMChain:
    """Async version of LLMChain."""

    def __init__(self, llm: AsyncCortexLLM, prompt, output_key: str = "text"):
        self.llm = llm
        self.prompt = prompt
        self.output_key = output_key

    async def ainvoke(self, inputs: Dict) -> Dict:
        formatted = self.prompt.format(**inputs)
        result = await self.llm.ainvoke(formatted)
        return {self.output_key: result.message, "_result": result}

    async def arun(self, **kwargs) -> str:
        result = await self.ainvoke(kwargs)
        return result[self.output_key]

    async def abatch(self, inputs_list: list, max_concurrency: int = 4) -> list:
        semaphore = asyncio.Semaphore(max_concurrency)

        async def _call(inputs):
            async with semaphore:
                return await self.ainvoke(inputs)

        return await asyncio.gather(*[_call(i) for i in inputs_list])

    async def __call__(self, inputs) -> Dict:
        if isinstance(inputs, str):
            inputs = {"input": inputs}
        return await self.ainvoke(inputs)

    def __repr__(self) -> str:
        return f"AsyncLLMChain(llm={self.llm!r}, output_key={self.output_key!r})"


class AsyncSequentialChain:
    """Runs a sequence of async chains, piping output from one to the next."""

    def __init__(self, chains: list, input_key: str = "input", output_key: str = "output"):
        self.chains = chains
        self.input_key = input_key
        self.output_key = output_key

    async def ainvoke(self, inputs: Dict) -> Dict:
        current = inputs
        for chain in self.chains:
            current = await chain.ainvoke(current)
        return current

    async def __call__(self, inputs) -> Dict:
        if isinstance(inputs, str):
            inputs = {self.input_key: inputs}
        return await self.ainvoke(inputs)

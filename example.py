"""
cortexchain usage examples
--------------------------
Run any section independently. All examples share the same agent_name.
"""
from cortexchain import (
    CortexLLM,
    PromptTemplate,
    LLMChain,
    ConversationChain,
    ConversationBufferMemory,
    ConversationWindowMemory,
    SimpleSequentialChain,
    tool,
    ReActAgent,
    AgentExecutor,
)

AGENT_NAME = "mydemo-prince-l103669"

# ---------------------------------------------------------------------------
# 1. Raw LLM call (drop-in replacement for llm_call.py)
# ---------------------------------------------------------------------------
llm = CortexLLM(agent_name=AGENT_NAME, default_knowledge=True)

response = llm("What is the capital of France?")
print("=== 1. Raw LLM ===")
print(response)

# ---------------------------------------------------------------------------
# 2. LLMChain — prompt template + LLM
# ---------------------------------------------------------------------------
print("\n=== 2. LLMChain ===")
prompt = PromptTemplate.from_template(
    "Translate the following text to Spanish:\n\n{text}"
)
chain = LLMChain(llm=llm, prompt=prompt)
print(chain.run(text="Good morning, how are you?"))

# Pipe syntax also works:
chain2 = PromptTemplate.from_template("Summarize in one sentence: {text}") | llm
print(chain2.run(text="LangChain is a framework for building LLM-powered applications."))

# ---------------------------------------------------------------------------
# 3. ConversationChain — automatic memory
# ---------------------------------------------------------------------------
print("\n=== 3. ConversationChain ===")
chat = ConversationChain(llm=llm, verbose=True)
chat.chat("Hi, my name is Alice.")
chat.chat("What is my name?")

# With a sliding window (remember last 3 exchanges)
windowed_memory = ConversationWindowMemory(k=3)
chat2 = ConversationChain(llm=llm, memory=windowed_memory)
print(chat2.chat("Tell me a joke."))

# ---------------------------------------------------------------------------
# 4. SimpleSequentialChain — chain multiple LLMChains
# ---------------------------------------------------------------------------
print("\n=== 4. SimpleSequentialChain ===")
step1 = LLMChain(
    llm=llm,
    prompt=PromptTemplate.from_template("Write a one-sentence synopsis for a movie about: {input}"),
)
step2 = LLMChain(
    llm=llm,
    prompt=PromptTemplate.from_template("Give this synopsis a catchy movie title:\n\n{text}"),
)
pipeline = SimpleSequentialChain(chains=[step1, step2], verbose=True)
print(pipeline.run("a robot who learns to paint"))

# ---------------------------------------------------------------------------
# 5. Tools + ReAct Agent
# ---------------------------------------------------------------------------
print("\n=== 5. Agent with tools ===")

@tool
def calculator(expression: str) -> str:
    """Evaluates a safe mathematical expression and returns the result."""
    allowed = set("0123456789+-*/(). ")
    if not all(c in allowed for c in expression):
        return "Error: unsafe expression."
    return str(eval(expression))  # noqa: S307  (safe — only digits/operators allowed)

@tool
def get_current_time(query: str) -> str:
    """Returns the current date and time. Ignores any input."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool(name="word_count", description="Counts the number of words in a given text.")
def word_count(text: str) -> str:
    return str(len(text.split()))

tools = [calculator, get_current_time, word_count]

agent = ReActAgent(llm=llm, tools=tools)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=8)

answer = executor.run("What is 123 multiplied by 456? Also, what time is it right now?")
print(f"\nFinal: {answer}")

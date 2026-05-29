"""Multi-agent debate — broadcast a prompt to several worker agents, let them
critique each other across rounds, score peers' responses (sentiment), and
have an impartial judge LLM synthesize the final verdict and reasoning path."""

import re
from typing import Any, Dict, List, Optional

from cortexchain.agents.supervisor import WorkerAgent
from cortexchain.llm.cortex import CortexLLM
from cortexchain.output_parsers.json_parser import JSONOutputParser

_OPENING_TEMPLATE = """\
You are {name}. {description}

A question has been put to you and a panel of peers. Give your best answer
based on your own perspective. Be specific and well-reasoned.

Question: {input}

Your answer:"""

_REBUTTAL_TEMPLATE = """\
You are {name}. {description}

You and a panel of peers were asked the same question. Below are your peers'
latest answers. Critique them where you disagree, acknowledge where they
strengthen your position, and refine your own answer accordingly.

Question: {input}

Peers' latest answers:
{peer_block}

Your refined answer:"""

_SENTIMENT_TEMPLATE = """\
You are {rater_name}. Read the following response from a peer ({ratee_name})
to a shared question, and rate it from your perspective.

Question: {input}

{ratee_name}'s response:
{ratee_response}

Respond with ONLY a valid JSON object (no prose, no markdown fence) using
exactly this schema:
{{"stance": "agree" | "disagree" | "neutral", "confidence": <float between 0 and 1>, "rationale": "<one short sentence>"}}
"""

_VERDICT_TEMPLATE = """\
You are an impartial judge. A panel of agents debated the following question
across {num_rounds} round(s). Below is the full transcript and the
cross-agent sentiment from the final round.

Question: {input}

Transcript:
{transcript}

Final-round sentiment matrix (rater -> ratee -> stance/confidence):
{sentiment_block}

Synthesize the best, most defensible answer. Respond using EXACTLY this
two-section format:

FINAL ANSWER:
<the optimal answer, standalone>

REASONING PATH:
<numbered steps explaining how you weighed the debaters' arguments and the
sentiment signals to arrive at the final answer>
"""


_FINAL_RE = re.compile(r"FINAL ANSWER:\s*(.*?)(?:REASONING PATH:|$)", re.IGNORECASE | re.DOTALL)
_REASONING_RE = re.compile(r"REASONING PATH:\s*(.*)", re.IGNORECASE | re.DOTALL)


class DebateAgent:
    """Runs a structured debate among `WorkerAgent`s and produces a judged verdict.

    Flow per `invoke()`:
      1. Opening round — every debater answers the prompt independently.
      2. Cross-sentiment — each debater rates every other debater's response.
      3. Rebuttal rounds — debaters see peers' last answers and refine.
      4. Verdict — the impartial `judge_llm` synthesizes a final answer plus
         a reasoning path that explains the route through the debate.

    Returns a dict with keys: `output`, `verdict`, `reasoning_path`, `rounds`,
    and `transcript`.
    """

    def __init__(
        self,
        judge_llm: CortexLLM,
        debaters: List[WorkerAgent],
        rounds: int = 2,
        verbose: bool = False,
    ):
        if len(debaters) < 2:
            raise ValueError("DebateAgent requires at least 2 debaters.")
        if rounds < 1:
            raise ValueError("rounds must be >= 1.")
        self.judge_llm = judge_llm
        self.debaters = debaters
        self.rounds = rounds
        self.verbose = verbose
        self._sentiment_parser = JSONOutputParser()

    def _rater_llm(self, worker: WorkerAgent) -> CortexLLM:
        """Use the worker's own LLM for sentiment so ratings reflect that
        agent's perspective. Fall back to the judge if not reachable."""
        llm = getattr(getattr(worker.executor, "agent", None), "llm", None)
        return llm if llm is not None else self.judge_llm

    def _peer_block(self, responses: Dict[str, str], excluding: str) -> str:
        parts = [f"- {name}: {resp}" for name, resp in responses.items() if name != excluding]
        return "\n".join(parts) if parts else "(no peer responses yet)"

    def _rate(self, rater: WorkerAgent, ratee_name: str, ratee_response: str, prompt: str) -> Dict[str, Any]:
        sentiment_prompt = _SENTIMENT_TEMPLATE.format(
            rater_name=rater.name,
            ratee_name=ratee_name,
            input=prompt,
            ratee_response=ratee_response,
        )
        raw = self._rater_llm(rater)(sentiment_prompt)
        try:
            parsed = self._sentiment_parser.parse(raw)
            stance = str(parsed.get("stance", "neutral")).lower().strip()
            if stance not in ("agree", "disagree", "neutral"):
                stance = "neutral"
            confidence = float(parsed.get("confidence", 0.0))
            confidence = max(0.0, min(1.0, confidence))
            rationale = str(parsed.get("rationale", "")).strip()
            return {"stance": stance, "confidence": confidence, "rationale": rationale}
        except (ValueError, TypeError):
            return {"stance": "neutral", "confidence": 0.0, "rationale": raw.strip()[:240]}

    def _score_round(self, responses: Dict[str, str], prompt: str) -> Dict[str, Dict[str, Dict[str, Any]]]:
        matrix: Dict[str, Dict[str, Dict[str, Any]]] = {}
        for rater in self.debaters:
            matrix[rater.name] = {}
            for ratee in self.debaters:
                if ratee.name == rater.name:
                    continue
                matrix[rater.name][ratee.name] = self._rate(
                    rater, ratee.name, responses[ratee.name], prompt
                )
        return matrix

    def _format_transcript(self, rounds_log: List[Dict[str, Any]]) -> str:
        chunks = []
        for r in rounds_log:
            chunks.append(f"--- Round {r['round']} ---")
            for name, resp in r["responses"].items():
                chunks.append(f"{name}: {resp}")
        return "\n".join(chunks)

    def _format_sentiment(self, matrix: Dict[str, Dict[str, Dict[str, Any]]]) -> str:
        lines = []
        for rater, ratees in matrix.items():
            for ratee, score in ratees.items():
                lines.append(
                    f"{rater} -> {ratee}: {score['stance']} "
                    f"(confidence={score['confidence']:.2f}) — {score['rationale']}"
                )
        return "\n".join(lines) if lines else "(no sentiment recorded)"

    def invoke(self, inputs: Dict) -> Dict[str, Any]:
        prompt = inputs.get("input", inputs.get("question", ""))
        rounds_log: List[Dict[str, Any]] = []
        last_responses: Dict[str, str] = {}

        for round_idx in range(self.rounds):
            round_num = round_idx + 1
            if self.verbose:
                print(f"\n[Debate Round {round_num}]")

            responses: Dict[str, str] = {}
            for worker in self.debaters:
                if round_idx == 0:
                    worker_prompt = _OPENING_TEMPLATE.format(
                        name=worker.name,
                        description=worker.description,
                        input=prompt,
                    )
                else:
                    worker_prompt = _REBUTTAL_TEMPLATE.format(
                        name=worker.name,
                        description=worker.description,
                        input=prompt,
                        peer_block=self._peer_block(last_responses, excluding=worker.name),
                    )
                response = worker.run(worker_prompt)
                responses[worker.name] = response
                if self.verbose:
                    print(f"  [{worker.name}]: {response[:200]}")

            sentiment = self._score_round(responses, prompt)
            if self.verbose:
                print(f"  [Sentiment]\n{self._format_sentiment(sentiment)}")

            rounds_log.append({"round": round_num, "responses": responses, "sentiment": sentiment})
            last_responses = responses

        transcript = self._format_transcript(rounds_log)
        final_sentiment_block = self._format_sentiment(rounds_log[-1]["sentiment"])
        verdict_prompt = _VERDICT_TEMPLATE.format(
            num_rounds=self.rounds,
            input=prompt,
            transcript=transcript,
            sentiment_block=final_sentiment_block,
        )
        verdict_raw = self.judge_llm(verdict_prompt)

        final_match = _FINAL_RE.search(verdict_raw)
        reasoning_match = _REASONING_RE.search(verdict_raw)
        if final_match:
            verdict = final_match.group(1).strip()
            reasoning_path = reasoning_match.group(1).strip() if reasoning_match else ""
        else:
            verdict = verdict_raw.strip()
            reasoning_path = ""

        if self.verbose:
            print(f"\n[Verdict]: {verdict}")

        return {
            "output": verdict,
            "verdict": verdict,
            "reasoning_path": reasoning_path,
            "rounds": rounds_log,
            "transcript": transcript,
        }

    def run(self, prompt: str) -> str:
        return self.invoke({"input": prompt})["output"]

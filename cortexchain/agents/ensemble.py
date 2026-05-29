"""Ensemble / voting agent — broadcast a prompt to N worker agents and pick a
single winning answer, either by majority vote across normalized responses
or by an impartial judge LLM. No debate, no rebuttal — just consensus."""

import re
from collections import Counter
from typing import Any, Dict, List, Optional

from cortexchain.agents.supervisor import WorkerAgent
from cortexchain.llm.cortex import CortexLLM

_JUDGE_TEMPLATE = """\
You are an impartial judge. {num_agents} agents independently answered the
following question. Pick the single best answer based on correctness,
clarity, and completeness.

Question: {input}

Candidate answers:
{candidate_block}

Respond with ONLY the name of the winning agent on the first line, then a
short one-sentence justification on the second line. Format:
WINNER: <agent name>
REASON: <one sentence>
"""

_WINNER_RE = re.compile(r"WINNER:\s*(.+?)(?:\n|$)", re.IGNORECASE)
_REASON_RE = re.compile(r"REASON:\s*(.+)", re.IGNORECASE | re.DOTALL)


class EnsembleAgent:
    """Broadcasts a prompt to a set of `WorkerAgent`s and selects one answer.

    Two voting modes:
      - `"judge"` (default): an impartial `judge_llm` picks the best candidate.
      - `"majority"`: normalized responses are tallied; the most common wins.
        Ties are broken by the judge if one is provided, otherwise the first
        agent in declaration order wins.

    Returns a dict with: `output`, `winner`, `reason`, `candidates`, `votes`.
    """

    def __init__(
        self,
        debaters: List[WorkerAgent],
        judge_llm: Optional[CortexLLM] = None,
        vote_method: str = "judge",
        verbose: bool = False,
    ):
        if len(debaters) < 2:
            raise ValueError("EnsembleAgent requires at least 2 agents.")
        if vote_method not in ("judge", "majority"):
            raise ValueError("vote_method must be 'judge' or 'majority'.")
        if vote_method == "judge" and judge_llm is None:
            raise ValueError("vote_method='judge' requires judge_llm.")
        self.debaters = debaters
        self.judge_llm = judge_llm
        self.vote_method = vote_method
        self.verbose = verbose

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text.lower().strip())

    def _format_candidates(self, candidates: Dict[str, str]) -> str:
        return "\n\n".join(f"[{name}]\n{resp}" for name, resp in candidates.items())

    def _judge_pick(self, candidates: Dict[str, str], prompt: str) -> Dict[str, str]:
        verdict_prompt = _JUDGE_TEMPLATE.format(
            num_agents=len(candidates),
            input=prompt,
            candidate_block=self._format_candidates(candidates),
        )
        raw = self.judge_llm(verdict_prompt)
        winner_match = _WINNER_RE.search(raw)
        reason_match = _REASON_RE.search(raw)

        winner_name = winner_match.group(1).strip() if winner_match else ""
        reason = reason_match.group(1).strip() if reason_match else raw.strip()

        resolved = None
        for name in candidates:
            if name.lower() == winner_name.lower() or name.lower() in winner_name.lower():
                resolved = name
                break
        if resolved is None:
            resolved = next(iter(candidates))
            reason = f"(judge response unparsable, defaulted to first agent) {reason}"
        return {"winner": resolved, "reason": reason}

    def _majority_pick(self, candidates: Dict[str, str], prompt: str) -> Dict[str, Any]:
        norm_to_names: Dict[str, List[str]] = {}
        for name, resp in candidates.items():
            norm_to_names.setdefault(self._normalize(resp), []).append(name)

        counts = Counter({norm: len(names) for norm, names in norm_to_names.items()})
        top_count = counts.most_common(1)[0][1]
        top_groups = [norm for norm, c in counts.items() if c == top_count]

        if len(top_groups) == 1:
            winner_name = norm_to_names[top_groups[0]][0]
            reason = f"Majority: {top_count}/{len(candidates)} agents agreed."
            votes = {norm_to_names[n][0]: c for n, c in counts.items()}
            return {"winner": winner_name, "reason": reason, "votes": votes}

        tied_candidates = {
            norm_to_names[n][0]: candidates[norm_to_names[n][0]] for n in top_groups
        }
        if self.judge_llm is not None:
            picked = self._judge_pick(tied_candidates, prompt)
            picked["reason"] = f"Tie among {len(tied_candidates)} answers — judge: {picked['reason']}"
            picked["votes"] = {norm_to_names[n][0]: c for n, c in counts.items()}
            return picked

        winner_name = next(iter(tied_candidates))
        return {
            "winner": winner_name,
            "reason": f"Tie among {len(tied_candidates)} answers — defaulted to first.",
            "votes": {norm_to_names[n][0]: c for n, c in counts.items()},
        }

    def invoke(self, inputs: Dict) -> Dict[str, Any]:
        prompt = inputs.get("input", inputs.get("question", ""))

        candidates: Dict[str, str] = {}
        for worker in self.debaters:
            response = worker.run(prompt)
            candidates[worker.name] = response
            if self.verbose:
                print(f"  [{worker.name}]: {response[:200]}")

        if self.vote_method == "judge":
            picked = self._judge_pick(candidates, prompt)
            votes: Dict[str, int] = {}
        else:
            picked = self._majority_pick(candidates, prompt)
            votes = picked.pop("votes", {})

        winner = picked["winner"]
        if self.verbose:
            print(f"\n[Winner]: {winner} — {picked['reason']}")

        return {
            "output": candidates[winner],
            "winner": winner,
            "reason": picked["reason"],
            "candidates": candidates,
            "votes": votes,
        }

    def run(self, prompt: str) -> str:
        return self.invoke({"input": prompt})["output"]

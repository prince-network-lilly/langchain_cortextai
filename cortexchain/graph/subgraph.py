"""Subgraph support — use a compiled graph as a node inside a parent graph."""

from typing import Callable, Dict, List, Optional
from cortexchain.graph.state_graph import CompiledGraph, StateGraph, END


class SubgraphNode:
    """Wraps a compiled StateGraph so it can be used as a node in a parent graph.

    Usage:
        inner_graph = StateGraph()
        inner_graph.add_node("step1", step1_fn)
        inner_graph.add_edge("step1", END)
        inner_graph.set_entry_point("step1")

        outer_graph = StateGraph()
        outer_graph.add_node("sub", SubgraphNode(inner_graph.compile()))
        outer_graph.add_edge("sub", END)
    """

    def __init__(
        self,
        graph: CompiledGraph,
        input_mapping: Optional[Dict[str, str]] = None,
        output_mapping: Optional[Dict[str, str]] = None,
    ):
        self.graph = graph
        self.input_mapping = input_mapping or {}
        self.output_mapping = output_mapping or {}

    def __call__(self, state: Dict) -> Dict:
        # Map parent state keys to subgraph input
        sub_state = state.copy()
        for parent_key, sub_key in self.input_mapping.items():
            if parent_key in state:
                sub_state[sub_key] = state[parent_key]

        # Execute subgraph
        result = self.graph.invoke(sub_state)

        # Map subgraph output back to parent state keys
        output = {}
        for sub_key, parent_key in self.output_mapping.items():
            if sub_key in result:
                output[parent_key] = result[sub_key]

        # If no output mapping, merge everything except internal keys
        if not self.output_mapping:
            output = {k: v for k, v in result.items() if not k.startswith("__")}

        return output


class ParallelNode:
    """Runs multiple functions/graphs in parallel (fan-out) and merges results (fan-in).

    Usage:
        parallel = ParallelNode(
            branches={
                "research": research_fn,
                "code": code_fn,
                "review": review_fn,
            }
        )
        graph.add_node("parallel_work", parallel)
    """

    def __init__(
        self,
        branches: Dict[str, Callable[[Dict], Dict]],
        merge_strategy: str = "merge_all",
    ):
        self.branches = branches
        self.merge_strategy = merge_strategy

    def __call__(self, state: Dict) -> Dict:
        results = {}
        # Execute all branches (sequentially — for true parallelism, use threading)
        for name, fn in self.branches.items():
            try:
                branch_result = fn(state.copy())
                if isinstance(branch_result, dict):
                    results[name] = branch_result
                else:
                    results[name] = {"output": branch_result}
            except Exception as e:
                results[name] = {"error": str(e)}

        # Merge results based on strategy
        if self.merge_strategy == "merge_all":
            merged = {"__parallel_results__": results}
            for name, result in results.items():
                for key, value in result.items():
                    merged[f"{name}_{key}"] = value
            return merged
        elif self.merge_strategy == "first_success":
            for name, result in results.items():
                if "error" not in result:
                    return result
            return {"error": "All branches failed", "__parallel_results__": results}
        else:
            return {"__parallel_results__": results}


class ParallelThreadedNode:
    """Same as ParallelNode but uses threading for true parallel execution."""

    def __init__(self, branches: Dict[str, Callable[[Dict], Dict]]):
        self.branches = branches

    def __call__(self, state: Dict) -> Dict:
        import concurrent.futures

        results = {}
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {name: executor.submit(fn, state.copy()) for name, fn in self.branches.items()}
            for name, future in futures.items():
                try:
                    result = future.result(timeout=120)
                    results[name] = result if isinstance(result, dict) else {"output": result}
                except Exception as e:
                    results[name] = {"error": str(e)}

        merged = {"__parallel_results__": results}
        for name, result in results.items():
            for key, value in result.items():
                merged[f"{name}_{key}"] = value
        return merged

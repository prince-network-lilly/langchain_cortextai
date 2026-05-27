from typing import Any, Callable, Dict, List, Optional, Union

END = "__end__"
START = "__start__"


class StateGraph:
    """
    LangGraph-style directed graph for orchestrating multi-step workflows.

    Usage:
        graph = StateGraph()
        graph.add_node("classify", classify_fn)
        graph.add_node("respond", respond_fn)
        graph.add_edge("classify", "respond")
        graph.add_edge("respond", END)
        graph.set_entry_point("classify")

        app = graph.compile()
        result = app.invoke({"input": "Hello"})
    """

    def __init__(self):
        self.nodes: Dict[str, Callable] = {}
        self.edges: Dict[str, Union[str, Callable]] = {}
        self.conditional_edges: Dict[str, Dict[str, Any]] = {}
        self.entry_point: Optional[str] = None

    def add_node(self, name: str, func: Callable[[Dict], Dict]) -> "StateGraph":
        """Add a node. func takes a state dict and returns an updated state dict."""
        self.nodes[name] = func
        return self

    def add_edge(self, from_node: str, to_node: str) -> "StateGraph":
        """Add a fixed edge from one node to another (or to END)."""
        self.edges[from_node] = to_node
        return self

    def add_conditional_edges(
        self,
        from_node: str,
        condition: Callable[[Dict], str],
        mapping: Optional[Dict[str, str]] = None,
    ) -> "StateGraph":
        """Add conditional routing from a node. condition(state) returns the next node name."""
        self.conditional_edges[from_node] = {
            "condition": condition,
            "mapping": mapping,
        }
        return self

    def set_entry_point(self, node_name: str) -> "StateGraph":
        """Set which node runs first."""
        self.entry_point = node_name
        return self

    def compile(self, checkpointer=None) -> "CompiledGraph":
        """Compile the graph into an executable."""
        if not self.entry_point:
            raise ValueError("Must set entry_point before compiling.")
        return CompiledGraph(
            nodes=self.nodes,
            edges=self.edges,
            conditional_edges=self.conditional_edges,
            entry_point=self.entry_point,
            checkpointer=checkpointer,
        )


class CompiledGraph:
    """A compiled, executable graph."""

    def __init__(
        self,
        nodes: Dict[str, Callable],
        edges: Dict[str, Union[str, Callable]],
        conditional_edges: Dict[str, Dict],
        entry_point: str,
        checkpointer=None,
    ):
        self.nodes = nodes
        self.edges = edges
        self.conditional_edges = conditional_edges
        self.entry_point = entry_point
        self.checkpointer = checkpointer

    def _get_next_node(self, current: str, state: Dict) -> Optional[str]:
        # Check conditional edges first
        if current in self.conditional_edges:
            cond_info = self.conditional_edges[current]
            condition = cond_info["condition"]
            mapping = cond_info.get("mapping")
            result = condition(state)
            if mapping:
                return mapping.get(result, result)
            return result

        # Check fixed edges
        if current in self.edges:
            return self.edges[current]

        return END

    def invoke(self, state: Dict, config: Optional[Dict] = None, max_steps: int = 50) -> Dict:
        """Execute the graph from entry point to END."""
        current_node = self.entry_point
        thread_id = (config or {}).get("thread_id", "default")

        # Restore from checkpoint if available
        if self.checkpointer:
            saved = self.checkpointer.load(thread_id)
            if saved:
                state.update(saved.get("state", {}))
                current_node = saved.get("next_node", current_node)

        step = 0
        while current_node != END and step < max_steps:
            if current_node not in self.nodes:
                raise ValueError(f"Node {current_node!r} not found in graph.")

            node_fn = self.nodes[current_node]
            result = node_fn(state)

            # Merge result into state
            if isinstance(result, dict):
                state.update(result)

            next_node = self._get_next_node(current_node, state)

            # Checkpoint after each step
            if self.checkpointer:
                self.checkpointer.save(
                    thread_id,
                    {
                        "state": state,
                        "current_node": current_node,
                        "next_node": next_node,
                        "step": step,
                    },
                )

            current_node = next_node
            step += 1

        state["__steps__"] = step
        return state

    def stream(self, state: Dict, config: Optional[Dict] = None, max_steps: int = 50):
        """Generator that yields state after each node execution."""
        current_node = self.entry_point
        step = 0

        while current_node != END and step < max_steps:
            if current_node not in self.nodes:
                raise ValueError(f"Node {current_node!r} not found in graph.")

            node_fn = self.nodes[current_node]
            result = node_fn(state)
            if isinstance(result, dict):
                state.update(result)

            yield {"node": current_node, "state": state.copy(), "step": step}

            current_node = self._get_next_node(current_node, state)
            step += 1

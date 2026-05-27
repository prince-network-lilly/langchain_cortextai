"""Human-in-the-loop — interrupt graph execution for human review/approval."""

from typing import Any, Callable, Dict, Optional


class HumanInterrupt(Exception):
    """Raised when a graph node requires human input before proceeding."""

    def __init__(self, message: str, node_name: str, state: Dict):
        self.message = message
        self.node_name = node_name
        self.state = state
        super().__init__(message)


class HumanApprovalNode:
    """A graph node that pauses execution for human approval.

    Usage in a StateGraph:
        approval = HumanApprovalNode(
            message="Deploy model v2.3 to production?",
            on_approve=lambda state: {**state, "approved": True},
            on_reject=lambda state: {**state, "approved": False},
        )
        graph.add_node("approval", approval)
    """

    def __init__(
        self,
        message: str = "Awaiting human approval...",
        input_key: str = "__human_input__",
        on_approve: Optional[Callable[[Dict], Dict]] = None,
        on_reject: Optional[Callable[[Dict], Dict]] = None,
        auto_approve: bool = False,
    ):
        self.message = message
        self.input_key = input_key
        self.on_approve = on_approve
        self.on_reject = on_reject
        self.auto_approve = auto_approve

    def __call__(self, state: Dict) -> Dict:
        if self.auto_approve:
            state["__human_decision__"] = "approve"
            if self.on_approve:
                return self.on_approve(state)
            return state

        # Check if human has already provided input
        if self.input_key in state:
            decision = state[self.input_key]
            if decision in ("approve", "yes", "y", "true", "1"):
                state["__human_decision__"] = "approve"
                if self.on_approve:
                    return self.on_approve(state)
            else:
                state["__human_decision__"] = "reject"
                if self.on_reject:
                    return self.on_reject(state)
            return state

        # No input yet — raise interrupt
        raise HumanInterrupt(
            message=self.message,
            node_name="human_approval",
            state=state,
        )


class InterruptibleGraph:
    """Wraps a CompiledGraph to handle human-in-the-loop interrupts gracefully.

    Usage:
        app = InterruptibleGraph(compiled_graph)
        try:
            result = app.invoke(state)
        except HumanInterrupt as interrupt:
            # Show message to user, get input
            decision = input(interrupt.message)
            # Resume with human input
            state[interrupt.node_name + "_input"] = decision
            result = app.resume(interrupt, decision)
    """

    def __init__(self, graph):
        self.graph = graph
        self._interrupted_state: Optional[Dict] = None
        self._interrupted_node: Optional[str] = None

    def invoke(self, state: Dict, config: Optional[Dict] = None) -> Dict:
        try:
            return self.graph.invoke(state, config)
        except HumanInterrupt as e:
            self._interrupted_state = e.state
            self._interrupted_node = e.node_name
            raise

    def resume(self, interrupt: HumanInterrupt, human_input: str) -> Dict:
        """Resume graph execution after human provides input."""
        state = interrupt.state.copy()
        state["__human_input__"] = human_input
        return self.graph.invoke(state)

    @property
    def is_interrupted(self) -> bool:
        return self._interrupted_state is not None


def require_approval(message: str = "Continue?"):
    """Decorator that makes a graph node require human approval before executing.

    Usage:
        @require_approval("Run expensive training job?")
        def train_model(state):
            ...
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(state: Dict) -> Dict:
            if state.get("__human_decision__") == "approve":
                state.pop("__human_decision__", None)
                return func(state)
            if "__human_input__" not in state:
                raise HumanInterrupt(
                    message=message,
                    node_name=func.__name__,
                    state=state,
                )
            decision = state.pop("__human_input__")
            if decision in ("approve", "yes", "y", "true", "1"):
                return func(state)
            state["__skipped__"] = func.__name__
            return state

        wrapper.__name__ = func.__name__
        return wrapper

    return decorator

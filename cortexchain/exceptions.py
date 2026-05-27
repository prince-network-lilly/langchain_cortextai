"""Custom exception hierarchy for cortexchain."""


class CortexChainError(Exception):
    """Base exception for all cortexchain errors."""

    pass


class LLMError(CortexChainError):
    """Raised when the LLM API call fails."""

    def __init__(self, message: str, status_code: int = None, raw_response=None):
        self.status_code = status_code
        self.raw_response = raw_response
        super().__init__(message)


class LLMConnectionError(LLMError):
    """Raised when the LLM API is unreachable."""

    pass


class LLMTimeoutError(LLMError):
    """Raised when the LLM API call times out."""

    pass


class LLMRateLimitError(LLMError):
    """Raised when the LLM API returns a rate limit response."""

    pass


class ChainError(CortexChainError):
    """Raised when a chain fails during execution."""

    def __init__(self, message: str, chain_name: str = "", inputs: dict = None):
        self.chain_name = chain_name
        self.inputs = inputs
        super().__init__(message)


class OutputParserError(CortexChainError):
    """Raised when output parsing fails."""

    def __init__(self, message: str, raw_output: str = ""):
        self.raw_output = raw_output
        super().__init__(message)


class ToolError(CortexChainError):
    """Raised when a tool execution fails."""

    def __init__(self, message: str, tool_name: str = "", tool_input: str = ""):
        self.tool_name = tool_name
        self.tool_input = tool_input
        super().__init__(message)


class GraphError(CortexChainError):
    """Raised when graph execution fails."""

    def __init__(self, message: str, node_name: str = "", state: dict = None):
        self.node_name = node_name
        self.state = state
        super().__init__(message)


class GraphNodeNotFoundError(GraphError):
    """Raised when a graph node is referenced but doesn't exist."""

    pass


class GraphCycleError(GraphError):
    """Raised when a graph has an infinite cycle."""

    pass


class ValidationError(CortexChainError):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str = "", value=None):
        self.field = field
        self.value = value
        super().__init__(message)


class ConfigError(CortexChainError):
    """Raised when configuration is invalid or missing."""

    pass


class RetryExhaustedError(CortexChainError):
    """Raised when all retry attempts have been exhausted."""

    def __init__(self, message: str, attempts: int = 0, last_error: Exception = None):
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(message)

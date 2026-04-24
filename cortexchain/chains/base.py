from abc import ABC, abstractmethod
from typing import Dict, Union


class BaseChain(ABC):
    """Abstract base for all chains."""

    @abstractmethod
    def invoke(self, inputs: Dict) -> Dict:
        pass

    def __call__(self, inputs: Union[Dict, str]) -> Dict:
        if isinstance(inputs, str):
            inputs = {self._default_input_key: inputs}
        return self.invoke(inputs)

    @property
    def _default_input_key(self) -> str:
        return "input"

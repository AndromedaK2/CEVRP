from dataclasses import dataclass, field
from typing import List


@dataclass
class Path:
    _nodes: List[str] = field(default_factory=list)
    _path_cost: float = 0.0

    @property
    def nodes(self) -> List[str]:
        return self._nodes

    @nodes.setter
    def nodes(self, value: List[str]) -> None:
        if not all(isinstance(node, str) for node in value):
            raise ValueError("All nodes must be strings.")
        self.nodes = value

    @property
    def path_cost(self) -> float:
        return self._path_cost

    @path_cost.setter
    def path_cost(self, value: float) -> None:
        if value < 0:
            raise ValueError("Path cost must be non-negative.")
        self._path_cost = value

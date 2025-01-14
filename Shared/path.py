import copy
from dataclasses import dataclass, field
from typing import List


@dataclass
class Path:
    _nodes: List[str] = field(default_factory=list)
    _path_cost: float = 0.0

    def __init__(self, nodes=None, path_cost=0.0):
        self.nodes = nodes or []
        self.path_cost = path_cost

    @property
    def nodes(self) -> List[str]:
        """Gets the list of nodes in the path."""
        return self._nodes

    @nodes.setter
    def nodes(self, value: List[str]) -> None:
        """Sets the list of nodes in the path, ensuring all are strings."""
        if not all(isinstance(node, str) for node in value):
            raise ValueError("All nodes must be strings.")
        self._nodes = value

    @property
    def path_cost(self) -> float:
        """Gets the cost of the path."""
        return self._path_cost

    @path_cost.setter
    def path_cost(self, value: float) -> None:
        """Sets the cost of the path, ensuring it is non-negative."""
        if value < 0:
            raise ValueError("Path cost must be non-negative.")
        self._path_cost = value

    def copy(self) -> "Path":
        """Creates a deep copy of the Path instance."""
        return Path(nodes=copy.deepcopy(self.nodes), path_cost=self.path_cost)

    def __str__(self) -> str:
        """Returns a string representation of the Path."""
        return f"Path(nodes={self.nodes}, path_cost={self.path_cost})"

    def __eq__(self, other: object) -> bool:
        """Checks equality based on nodes and path_cost."""
        if not isinstance(other, Path):
            return NotImplemented
        return self.nodes == other.nodes and self.path_cost == other.path_cost

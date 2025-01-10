from dataclasses import dataclass, field
from typing import List


@dataclass
class Path:
    _nodes: List[str] = field(default_factory=list)
    _path_cost: float = 0.0

    @property
    def nodes(self) -> List[str]:
        """
        Gets the list of nodes in the path.
        """
        return self._nodes

    @nodes.setter
    def nodes(self, value: List[str]) -> None:
        """
        Sets the list of nodes in the path, ensuring all are strings.

        :param value: A list of strings representing nodes.
        :raises ValueError: If any element in the list is not a string.
        """
        if not all(isinstance(node, str) for node in value):
            raise ValueError("All nodes must be strings.")
        self._nodes = value  # Assign to the private attribute

    @property
    def path_cost(self) -> float:
        """
        Gets the cost of the path.
        """
        return self._path_cost

    @path_cost.setter
    def path_cost(self, value: float) -> None:
        """
        Sets the cost of the path, ensuring it is non-negative.

        :param value: A float representing the path cost.
        :raises ValueError: If the cost is negative.
        """
        if value < 0:
            raise ValueError("Path cost must be non-negative.")
        self._path_cost = value  # Assign to the private attribute

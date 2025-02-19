from dataclasses import dataclass, field
from typing import List
import copy

@dataclass
class Path:
    _nodes: List[str] = field(default_factory=list, repr=False)
    _path_cost: float = 0.0
    _demand: int = 0
    _energy: float = 0.0
    _feasible: bool = False

    def __init__(self, nodes: List[str] = None, path_cost: float = 0.0, demand: int = 0, energy: float = 0.0, feasible: bool = False):
        self.nodes = nodes if nodes else []
        self.path_cost = path_cost
        self.demand = demand
        self.energy = energy
        self.feasible = feasible


    @property
    def feasible(self) -> bool:
        return self._feasible

    @feasible.setter
    def feasible(self, value):
        self._feasible = value

    @property
    def nodes(self) -> List[str]:
        return self._nodes

    @nodes.setter
    def nodes(self, value: List[str]) -> None:
        if not isinstance(value, list) or not all(isinstance(node, str) for node in value):
            raise ValueError("All nodes must be strings.")
        self._nodes = value

    @property
    def path_cost(self) -> float:
        return self._path_cost

    @path_cost.setter
    def path_cost(self, value: float) -> None:
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError("Path cost must be a non-negative number.")
        self._path_cost = float(value)

    @property
    def demand(self) -> int:
        return self._demand

    @demand.setter
    def demand(self, value: int) -> None:
        """Sets the demand, ensuring it is a non-negative integer."""
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValueError("Demand must be a non-negative integer.")

        if value < 0:
            raise ValueError("Demand must be a non-negative integer.")

        self._demand = value

    @property
    def energy(self) -> float:
        return self._energy

    @energy.setter
    def energy(self, value: float) -> None:
        """Sets the demand, ensuring it is a non-negative integer."""
        self._energy = value

    def copy(self) -> "Path":
        """Creates a deep copy of the Path instance."""
        return Path(
            nodes=copy.deepcopy(self.nodes),
            path_cost=copy.deepcopy(self.path_cost),
            demand=copy.deepcopy(self.demand),
            energy=copy.deepcopy(self.energy),
            feasible=copy.deepcopy(self.feasible),
        )

    def __str__(self) -> str:
        return f"Path(nodes={self.nodes}, path_cost={self.path_cost}, demand={self.demand}, energy={self.energy}), feasible={self.feasible}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Path):
            return NotImplemented
        return (self.nodes == other.nodes and self.path_cost == other.path_cost and self.demand == other.demand
                and self.energy == other.energy and self.feasible == other.feasible)



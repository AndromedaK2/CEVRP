from dataclasses import dataclass, field
from typing import List, Tuple
import networkx as nx
from MMAS.ant import Ant
from Shared.cevrp import CEVRP
from Shared.graph_api import GraphApi
from Shared.path import Path


@dataclass
class ACO:
    graph: nx.DiGraph
    max_ant_steps: int  # Maximum number of steps an ant is allowed to take to reach the destination
    num_iterations: int  # Number of cycles/waves of search ants to be deployed
    evaporation_rate: float = 0.98  # Evaporation rate (rho)
    pheromone_importance: float = 1.0  # Pheromone bias (alpha)
    cost_importance: float = 2.0  # Edge cost bias (beta)
    search_ants: List[Ant] = field(default_factory=list)  # Search ants
    max_pheromone_level: float = 1.0  # limit τ_max
    best_path: List[Path] = field(default_factory=list)  # best global solution
    best_path_cost: float = 0.0  # best global solution path
    second_best_path: List[Path] = field(default_factory=list)  # second-best global solution
    second_best_path_cost: float = float('inf')  # second-best global solution path cost
    cevrp: CEVRP = field(default_factory=CEVRP)  # CEVRP instance

    def __post_init__(self):
        self.graph_api = GraphApi(self.graph, self.evaporation_rate)
        self._initialize_pheromones()

    def _initialize_pheromones(self):
        """Initialize all edges of the graph with a maximum pheromone value."""
        for edge in self.graph.edges:
            self.graph_api.set_edge_pheromones(edge[0], edge[1], self.max_pheromone_level)

    def find_shortest_path(self, start: str, num_ants: int) -> Tuple[List[str], float, List[Path]]:
        """Finds the shortest path from the start to the destination in the graph."""
        self._deploy_search_ants(start, num_ants)
        if not self.best_path or self._calculate_path_cost(self.best_path) != self.best_path_cost:
            # If the best path cost is inconsistent, use the second-best path if available
            if self.second_best_path and self.second_best_path_cost != float('inf'):
                return self._flatten_path(self.second_best_path), self.second_best_path_cost, self.second_best_path
            return [], float('inf'), []  # If no second-best path exists, return default values
        return self._flatten_path(self.best_path), self.best_path_cost, self.best_path

    def _deploy_search_ants(self, start: str, num_ants: int) -> None:
        """Deploy search ants that traverse the graph to find the shortest path."""
        for _ in range(self.num_iterations):
            self._initialize_ants(start, num_ants)
            self._deploy_forward_search()
            self._deploy_backward_search()

    def _initialize_ants(self, start: str, num_ants: int):
        """Initialize ants at the start position."""
        self.search_ants.clear()
        for _ in range(num_ants):
            ant = Ant(
                self.graph_api,
                start,
                alpha=self.pheromone_importance,
                beta=self.cost_importance,
                evaporation_rate=self.evaporation_rate,
                best_path_cost=self.best_path_cost,
                cevrp=self.cevrp,
            )
            self.search_ants.append(ant)

    def _deploy_forward_search(self) -> None:
        """Deploy forward search ants in the graph."""
        for ant in self.search_ants:
            self._ant_exploration(ant)

    def _ant_exploration(self, ant: Ant):
        """Ant explores the graph for a potential path."""
        for _ in range(self.max_ant_steps):
            ant.take_step()
            # Stop Criteria
            if ant.reached_destination():
                ant.is_fit = True
                break
        self._update_best_path(ant)

    def _update_best_path(self, ant: Ant):
        """Update the best and second-best path discovered by the ants."""
        if ant.path_cost < self.best_path_cost:
            self.second_best_path_cost, self.second_best_path = self.best_path_cost, self.best_path.copy()
            self.best_path_cost, self.best_path = ant.path_cost, ant.paths.copy()
            ant.best_path_cost = ant.path_cost
        elif ant.path_cost < self.second_best_path_cost:
            self.second_best_path_cost, self.second_best_path = ant.path_cost, ant.paths.copy()
            ant.best_path_cost = ant.path_cost

    def _deploy_backward_search(self) -> None:
        """Deploy fit search ants back towards their source node while dropping pheromones on the path."""
        for ant in self.search_ants:
            if ant.is_fit:
                ant.deposit_pheromones_on_paths()

    @staticmethod
    def _flatten_path(paths: List[Path]) -> List[str]:
        """Flatten the nodes in the provided paths into a single list."""
        return [node for path in paths for node in path.nodes]

    @staticmethod
    def _calculate_path_cost(paths: List[Path]) -> float:
        """Calculate the total cost of the provided paths."""
        return sum(path.path_cost for path in paths)

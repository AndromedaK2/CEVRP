import math
import time
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
    max_ant_steps: int
    num_iterations: int
    evaporation_rate: float = 0.98
    pheromone_importance: float = 1.0
    cost_importance: float = 2.0
    search_ants: List[Ant] = field(default_factory=list)
    max_pheromone_level: float = 1.0
    best_path: List[Path] = field(default_factory=list)
    best_path_cost: float = float('inf')
    second_best_path: List[Path] = field(default_factory=list)
    second_best_path_cost: float = float('inf')
    current_best_path_cost: float = float('inf')
    last_best_path_cost: float = float('inf')
    cevrp: CEVRP = field(default_factory=CEVRP)
    max_iteration_improvement: int = 100
    max_iteration_improvement_counter: int = 0
    exec_time: float = 0.0
    use_route_construction: bool = False


    def __post_init__(self):
        if not self.graph:
            raise ValueError("Graph must be provided.")
        self.graph_api = GraphApi(self.graph)
        self.max_iteration_improvement_counter = self.max_iteration_improvement
        self._initialize_pheromones()

    def _initialize_pheromones(self):
        """
        Initialize all edges of the graph with a maximum pheromone value.
        """
        for edge in self.graph.edges:
            self.graph_api.set_edge_pheromones(edge[0], edge[1], self.max_pheromone_level)

    def find_shortest_path(self, start: str, num_ants: int) -> Tuple[List[str], float, List[Path]]:
        """
        Finds the shortest path from the start to the destination in the graph.
        """
        self._deploy_search_ants(start, num_ants)
        return self._get_best_solution_found()


    def _deploy_search_ants(self, start: str, num_ants: int) -> None:
        """
        Deploy search ants that traverse the graph to find the shortest path.

        Args:
            start (str): The starting node for the ants.
            num_ants (int): The number of ants to deploy.
        """
        for _ in range(self.num_iterations):
            self._initialize_ants(start, num_ants)
            self._deploy_forward_search()
            self._deploy_backward_search()
            self._found_better_solution()

            current_time = time.time()
            elapsed_minutes = round((self.exec_time - current_time) / 60)

            print(f"Rest time: {elapsed_minutes} minutes", end="\r", flush=True)

            if self.max_iteration_improvement_counter <= 0 or current_time >= self.exec_time:
                break


    def _initialize_ants(self, start: str, num_ants: int):
        """
        Initialize ants at the start position.

        Args:
            start (str): The starting node for the ants.
            num_ants (int): The number of ants to deploy.
        """
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
        """
        Deploy forward search ants in the graph.
        """
        for ant in self.search_ants:
            self._ant_exploration(ant)

    def _ant_exploration(self, ant: Ant):
        """
        Ant explores the graph for a potential path.

        Args:
            ant (Ant): The ant to explore the graph.
        """

        for _ in range(self.max_ant_steps):
            ant.take_step()  # Use step-by-step exploration strategy
            if ant.reached_destination(self.use_route_construction):
                if self._are_valid_paths(ant.paths):
                    ant.is_fit = True
                break

        # Update the best path based on the ant's exploration
        self._update_best_path(ant)

    def _update_best_path(self, ant: Ant):
        """
        Update the best and second-best path discovered by the ants.

        Args:
            ant (Ant): The ant whose path is being evaluated.
        """
        if not ant.is_fit:
            return
        if ant.path_cost < self.best_path_cost:
            self.second_best_path_cost, self.second_best_path = self.best_path_cost, self.best_path.copy()
            self.best_path_cost, self.best_path = ant.path_cost, ant.paths.copy()
        elif ant.path_cost < self.second_best_path_cost:
            self.second_best_path_cost, self.second_best_path = ant.path_cost, ant.paths.copy()
            self.current_best_path_cost = self.second_best_path_cost
        else:
            ant.is_fit = False


    def _deploy_backward_search(self) -> None:
        """
        Deploy fit search ants back towards their source node while dropping pheromones on the path.
        """
        for ant in self.search_ants:
            if ant.is_fit:
                ant.deposit_pheromones_on_paths()

    def _found_better_solution(self):
        if self.current_best_path_cost < self.last_best_path_cost:
            self.last_best_path_cost = self.current_best_path_cost
            self.max_iteration_improvement_counter = self.max_iteration_improvement
        else:
            self.max_iteration_improvement -= 1

    def _get_best_solution_found(self):
        value = 0
        if self.best_path.count != 0:
            value = self.graph_api.calculate_paths_cost(self.best_path)

        def are_equal(a: float, b: float) -> bool:
            tolerance = 1e-12
            if math.isinf(a) and math.isinf(b):
                return True
            return math.isclose(a, b, rel_tol=tolerance, abs_tol=tolerance)

        if not self.best_path or not are_equal(value, self.best_path_cost):
            if self.second_best_path and not math.isinf(self.second_best_path_cost):
                return (
                    self._flatten_path(self.second_best_path),
                    self.second_best_path_cost,
                    self.second_best_path
                )
            return [], float('inf'), []

        return (
            self._flatten_path(self.best_path),
            self.best_path_cost,
            self.best_path
        )

    @staticmethod
    def _are_valid_paths(paths: List[Path]) -> bool:
        for path in paths:
            if len(path.nodes) <= 4:
                return False
        return True

    @staticmethod
    def _flatten_path(paths: List[Path]) -> List[str]:
        """
        Flatten the nodes in the provided paths into a single list
        """
        return [node for path in paths for node in path.nodes]

from dataclasses import dataclass, field, Field
from typing import List, Tuple
import networkx as nx

from MMAS.ant import Ant
from Shared.evrp import EVRP
from Shared.graph_api import GraphApi
from MMAS.path import Path


@dataclass
class ACO:
    graph: nx.DiGraph
    # Maximum number of steps an ant is allowed is to take in order to reach the destination
    ant_max_steps: int
    # Number of cycles/waves of search ants to be deployed
    num_iterations: int
    # Evaporation rate (rho)
    evaporation_rate: float = 0.98
    # Pheromone bias
    alpha: float = 1.0
    # Edge cost bias
    beta: float = 2.0
    # Search ants
    search_ants: List[Ant] = field(default_factory=list)
    # limit τ_max
    max_pheromone_level: float = 1.0
    # best global solution
    best_path: List[Path] = field(default_factory=list)
    # best global solution path
    best_path_cost: float = 0.0
    # best global solution
    second_best_path: List[Path] = field(default_factory=list)
    # best global solution path
    second_best_path_cost: float = float('inf')
    # evrp instance
    evrp_instance: EVRP = field(default_factory=EVRP)

    def __post_init__(self):
        self.graph_api = GraphApi(self.graph, self.evaporation_rate)
        # Initialize all edges of the graph with a maximum pheromone value
        for edge in self.graph.edges:
            self.graph_api.set_edge_pheromones(edge[0], edge[1], self.max_pheromone_level)

    def find_shortest_path(
            self,
            source: str,
            num_ants: int,
    ) -> Tuple[List[str], float]:
        """Finds the shortest path from the source to the destination in the graph.

        Args:
            source (str): The source node in the graph.
            num_ants (int): The number of search ants to be deployed.

        Returns:
            Tuple[List[str], float]: A list of concatenated nodes as strings and the total cost.
        """
        # Deploy search ants to explore the graph
        self._deploy_search_ants(source, num_ants)


        # Validate the consistency of the best path's cost
        calculated_cost = sum(path.path_cost for path in self.best_path)
        if self.best_path.count == 0 or calculated_cost != self.best_path_cost:
            # If the best path cost is inconsistent, use the second-best path if available
            if self.second_best_path and self.second_best_path_cost != float('inf'):
                flattened_nodes = [node for path in self.second_best_path for node in path.nodes]
                return flattened_nodes, self.second_best_path_cost
            # If no second-best path exists, return default values
            return [], float('inf')

        # If the best path cost is consistent, return it
        flattened_nodes = [node for path in self.best_path for node in path.nodes]
        return flattened_nodes, self.best_path_cost

    def _deploy_search_ants(
            self,
            source: str,
            num_ants: int,
    ) -> None:
        """Deploy search ants that traverse the graph to find the shortest path

        Args:
            source (str): The source node in the graph
            num_ants (int): The number of ants to be spawned
        """
        for _ in range(self.num_iterations):
            self.search_ants.clear()

            for _ in range(num_ants):
                spawn_point = source

                ant = Ant(
                    self.graph_api,
                    spawn_point,
                    alpha=self.alpha,
                    beta=self.beta,
                    evaporation_rate = self.evaporation_rate,
                    best_path_cost=self.best_path_cost,
                    evrp_instance=self.evrp_instance,
                )
                self.search_ants.append(ant)

            self._deploy_forward_search_ants()
            self._deploy_backward_search_ants()

    def _deploy_forward_search_ants(self) -> None:
        """Deploy forward search ants in the graph"""
        for ant in self.search_ants:
            for _ in range(self.ant_max_steps):
                ant.take_step()
                """Stop Criteria"""
                if ant.reached_destination():
                    ant.is_fit = True
                    break
            if ant.path_cost < self.best_path_cost:
                self.second_best_path_cost = self.best_path_cost
                self.second_best_path = self.best_path.copy()
                self.best_path_cost = ant.path_cost
                self.best_path = ant.paths.copy()
            elif ant.path_cost < self.second_best_path_cost:
                self.second_best_path_cost = ant.path_cost
                self.second_best_path = ant.paths.copy()

    def _deploy_backward_search_ants(self) -> None:
        """Deploy fit search ants back towards their source node while dropping pheromones on the path"""
        for ant in self.search_ants:
            if ant.is_fit:
                ant.deposit_pheromones_on_paths()


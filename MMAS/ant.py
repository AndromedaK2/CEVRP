from dataclasses import dataclass, field
from typing import Dict, List, Set

from MMAS import utils
from MMAS.constants import *
from MMAS.graph_api import GraphApi
from MMAS.path import Path

@dataclass
class Ant:
    graph_api: GraphApi
    source: str
    # Pheromone bias
    alpha: float = 0.7
    # Edge cost bias
    beta: float = 0.3
    # Set of nodes that have been visited by the ant
    visited_nodes: Set = field(default_factory=set)
    # Path taken by the ant so far
    path: Path = field(default_factory=Path)
    # All Paths taken by the ant so far
    paths: List[Path] = field(default_factory=list)
    # Cost of the path taken by the ant so far
    path_cost: float = 0.0
    # Indicates if the ant has reached the destination (fit) or not (unfit)
    is_fit: bool = False
    # Indicates if the ant is the pheromone-greedy solution ant
    is_solution_ant: bool = False
    # Variable Indicates the max capacity
    limit_load_current_vehicle: float = 0
    # Indicates the capacity of all customers
    total_capacity_customers: int = 0
    # Quantity of vehicles used at the moment
    vehicle_counter: int = 0
    # Current Node
    current_node: str = ""

    def __post_init__(self) -> None:
        # Set the spawn node as the current and first node
        self.current_node = self.source
        self.path.nodes.append(self.source)

    def reached_destination(self) -> bool:
        """Returns if the ant has reached the destination node in the graph

        Returns:
            bool: returns True if the ant has reached the destination
        """
        return self.current_node == self.source

    def take_step(self) -> None:
        """Compute and update the ant position"""

        # Pick the next node of the ant
        next_node = self._choose_next_node()

        self.path.nodes.append(next_node)
        if next_node == self.source:
            # add path to candidate solution of paths
            self.paths.append(self.path)
            self.limit_load_current_vehicle = 0
            self.vehicle_counter += 1
        else:
            # Mark the current node as visited
            self.visited_nodes.add(self.current_node)
            self.path_cost += self.graph_api.get_edge_cost(self.current_node, next_node)
            self.path.path_cost += self.path_cost
            self.limit_load_current_vehicle += self.graph_api.get_demand_node(next_node)
            self.current_node = next_node

    def _choose_next_node(self) -> int | str:
        """Choose the next node to be visited by the ant

        Returns:
            [str, None]: The computed next node to be visited by the ant or None if no possible moves
        """

        unvisited_neighbors = self._get_unvisited_neighbors_with_demand()

        if self.is_solution_ant:
            if len(unvisited_neighbors) == 0:
                raise Exception(f"No path found from {self.source}")
            return max(
                unvisited_neighbors,
                key=lambda neighbor: self.graph_api.get_edge_pheromones(self.current_node, neighbor['node'])
            )['node']

        # Check if ant has no possible nodes to move to
        if len(unvisited_neighbors) == 0:
            return self.source

        if self._get_total_demand_of_neighbors(unvisited_neighbors) <= LOAD_LIMIT_VEHICLE * (FLEET - self.vehicle_counter - 1):
            return self.source

        probabilities = self._calculate_edge_probabilities(unvisited_neighbors)

        # Pick the next node based on the roulette wheel selection technique
        return utils.roulette_wheel_selection(probabilities)

    def _get_unvisited_neighbors_with_demand(self) -> List[Dict[str, int]]:
        """Returns a list of unvisited neighbors of the current node, along with each neighbor's demand.

        Returns:
            List[Dict[str, int]]: A list of dictionaries containing each unvisited neighbor and its demand.
        """
        unvisited_neighbors_with_demand = []

        neighbors_with_demand = self.graph_api.get_neighbors_with_demand(self.current_node)

        for neighbor_info in neighbors_with_demand:
            if (neighbor_info['node'] not in self.visited_nodes and
                    neighbor_info['demand'] <=  LOAD_LIMIT_VEHICLE - self.limit_load_current_vehicle):
                unvisited_neighbors_with_demand.append(neighbor_info)

        return unvisited_neighbors_with_demand

    def _get_total_demand_of_neighbors(self,neighbors_with_demand: List[Dict[str, int]]) -> int:
        """Calculates and returns the total demand of a given list of neighbors.

        Args:
            neighbors_with_demand (List[Dict[str, int]]): A list of dictionaries containing each neighbor and its demand.

        Returns:
            int: The sum of the demands of all the given neighbors.
        """
        return sum(neighbor_info['demand'] for neighbor_info in neighbors_with_demand)

    def deposit_pheromones_on_paths(self) -> None:
        """Updates the pheromones along all the edges in the paths."""
        for path in self.paths:  # Itera sobre cada ruta en la lista paths
            for i in range(len(path.nodes) - 1):
                u, v = path.nodes[i], path.nodes[i + 1]
                new_pheromone_value = 1 / path.path_cost  # Asegúrate de que cada path tenga un atributo path_cost
                self.graph_api.deposit_pheromones(u, v, new_pheromone_value)

    def _compute_all_edges_desirability(
            self,
            neighbors_with_demand: List[Dict[str, int]],
    ) -> float:
        """Computes the denominator of the transition probability equation for the ant

        Args:
            unvisited_neighbors (List[str]): All unvisited neighbors of the current node

        Returns:
            float: The summation of all the outgoing edges (to unvisited nodes) from the current node
        """
        total = 0.0
        for neighbor in neighbors_with_demand:
            edge_pheromones = self.graph_api.get_edge_pheromones(
                self.current_node, str(neighbor['node'])
            )
            edge_cost = self.graph_api.get_edge_cost(self.current_node, str(neighbor['node']))
            total += utils.compute_edge_desirability(
                edge_pheromones, edge_cost, self.alpha, self.beta
            )

        return total

    def _calculate_edge_probabilities(
            self, neighbors_with_demand: List[Dict[str, int]],
    ) -> Dict[str, float]:
        """Computes the transition probabilities of all the edges from the current node

        Args:
            unvisited_neighbors (List[str]): A list of unvisited neighbors of the current node

        Returns:
            Dict[str, float]: A dictionary mapping nodes to their transition probabilities
        """
        probabilities: Dict[str, float] = {}

        all_edges_desirability = self._compute_all_edges_desirability(
            neighbors_with_demand
        )

        for neighbor in neighbors_with_demand:
            edge_pheromones = self.graph_api.get_edge_pheromones(
                self.current_node, str(neighbor['node'])
            )
            edge_cost = self.graph_api.get_edge_cost(self.current_node, str(neighbor['node']))

            current_edge_desirability = utils.compute_edge_desirability(
                edge_pheromones, edge_cost, self.alpha, self.beta
            )
            probabilities[str(neighbor['node'])] = current_edge_desirability / all_edges_desirability

        return probabilities

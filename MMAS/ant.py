from dataclasses import dataclass, field
from typing import Dict, List, Set

from MMAS import pheromone_operators
from Shared.cevrp import CEVRP
from Shared.graph_api import GraphApi
from MMAS.path import Path


@dataclass
class Ant:
    graph_api: GraphApi
    source: str
    alpha: float = 0.7
    beta: float = 0.3
    evaporation_rate: float = 0.98
    visited_nodes: Set = field(default_factory=set)
    path: Path = field(default_factory=Path)
    paths: List[Path] = field(default_factory=list)
    path_cost: float = 0.0
    is_fit: bool = False
    limit_load_current_vehicle: float = 0
    total_capacity_customers: int = 0
    vehicle_counter: int = 0
    current_node: str = ""
    best_path_cost: float = 0
    cevrp: CEVRP = field(default_factory=CEVRP)

    def __post_init__(self) -> None:
        # Set the spawn node as the current and first node
        self.current_node = self.source
        self.path.nodes.append(self.source)

    def reached_destination(self) -> bool:
        """Checks if the ant has visited all nodes in the graph.

        Returns:
            bool: True if the ant has visited all required nodes, otherwise False.
        """
        total_visited_nodes = len(self.visited_nodes)
        total_nodes = len(self.graph_api.graph.nodes)
        return total_visited_nodes >= total_nodes

    def take_step(self) -> None:
        """Compute and update the ant position"""

        # Pick the next node of the ant
        next_node = self._choose_next_node()

        self.path.nodes.append(next_node)
        self.visited_nodes.add(self.current_node)

        if next_node == self.source:
            # add path to candidate solution of paths
            self.paths.append(self.path)
            self.path = Path()
            self.path.nodes.append(next_node)
            self.limit_load_current_vehicle = 0
            self.vehicle_counter += 1
        else:
            # Mark the current node as visited
            edge_cost = self.calculate_edge_cost(next_node)

            self.path_cost += edge_cost
            self.path.path_cost += edge_cost
            self.limit_load_current_vehicle += self.graph_api.get_demand_node(next_node)
            self.current_node = next_node

    def calculate_edge_cost(self, next_node: str) -> float:
        """Calculate the cost of the edge from the current node to the next node."""
        return self.graph_api.get_edge_cost(self.current_node, next_node)

    def _choose_next_node(self) -> str:
        """Choose the next node to be visited by the ant"""

        unvisited_neighbors = self._get_unvisited_neighbors_with_demand()
        remaining_vehicle_cap = self.cevrp.capacity * (self.cevrp.vehicles - self.vehicle_counter - 1)
        total_neighbors_demand = self.graph_api.get_total_demand_of_neighbors(unvisited_neighbors)

        if total_neighbors_demand <= remaining_vehicle_cap or not unvisited_neighbors:
            unvisited_neighbors.append({'node': self.source, 'demand': 0})

        edge_probabilities = self._calculate_edge_probabilities(unvisited_neighbors)

        # Pick the next node based on the roulette wheel selection technique
        return pheromone_operators.roulette_wheel_selection(edge_probabilities)

    def _get_unvisited_neighbors_with_demand(self) -> List[Dict[str, int]]:
        """Returns a list of unvisited neighbors of the current node, along with each neighbor's demand.

        Returns:
            List[Dict[str, int]]: A list of dictionaries containing each unvisited neighbor and its demand.
        """
        unvisited_neighbors_with_demand = []

        neighbors_with_demand = self.graph_api.get_neighbors_with_demand(self.current_node)

        for neighbor_info in neighbors_with_demand:
            if (neighbor_info['node'] not in self.visited_nodes and
                    neighbor_info['demand'] <= self.cevrp.capacity - self.limit_load_current_vehicle):
                unvisited_neighbors_with_demand.append(neighbor_info)

        return unvisited_neighbors_with_demand

    def deposit_pheromones_on_paths(self) -> None:
        """Updates the pheromones along all the edges in the paths."""
        for path in self.paths:
            for i in range(len(path.nodes) - 1):
                u, v = path.nodes[i], path.nodes[i + 1]
                new_pheromone_value = pheromone_operators.calculate_pheromone_value(self.evaporation_rate,
                                                                                    self.graph_api.get_edge_pheromones(
                                                                                        u, v),
                                                                                    self.best_path_cost,
                                                                                    self.graph_api.get_length_graph())
                self.graph_api.deposit_pheromones(u, v, new_pheromone_value)

    def _compute_all_edges_desirability(
            self,
            neighbors_with_demand: List[Dict[str, int]],
    ) -> float:
        """Computes the denominator of the transition probability equation for the ant

        Args:
            neighbors_with_demand (List[str]): All unvisited neighbors of the current node

        Returns:
            float: The summation of all the outgoing edges (to unvisited nodes) from the current node
        """
        total = 0.0
        for neighbor in neighbors_with_demand:
            edge_pheromones = self.graph_api.get_edge_pheromones(
                self.current_node, str(neighbor['node'])
            )
            edge_cost = self.graph_api.get_edge_cost(self.current_node, str(neighbor['node']))
            total += pheromone_operators.compute_edge_desirability(
                edge_pheromones, edge_cost, self.alpha, self.beta
            )

        return total

    def _calculate_edge_probabilities(
            self, unvisited_neighbors: List[Dict[str, int]],
    ) -> Dict[str, float]:
        """
        Calculates the transition probabilities of all edges from the current node.

        Formula to calculate the probability of selecting edge (i, j):
                             (φᵢⱼ)^α
            pᵢⱼ = ---------------------------
                   Σₖ∈V𝚌 (φᵢₖ)^α / (dᵢₖ)^β
        Where:
         - V𝚌: Set of neighboring nodes of i.
         - φᵢⱼ: Pheromone value on the edge (i, j).
         - dᵢⱼ: Cost or distance associated with the edge (i, j).
         - α: Exponent controlling the influence of the pheromone.
         - β: Exponent controlling the influence of the cost or distance.

        Args:
            unvisited_neighbors (List[Dict[str, int]]): A list of unvisited neighbors with demand.

        Returns:
            Dict[str, float]: A dictionary mapping nodes to their transition probabilities.
        """
        NODE = 'node'
        edge_probabilities: Dict[str, float] = {}

        # Compute the total desirability of all edges based on unvisited neighbors
        total_desirability = self._compute_all_edges_desirability(unvisited_neighbors)

        for neighbor in unvisited_neighbors:
            node_identifier = str(neighbor[NODE])

            # Calculate the desirability of a specific edge to the target node
            edge_desirability = self._get_edge_desirability(node_identifier)

            # Calculate the transition probability by normalizing with total desirability
            edge_probabilities[node_identifier] = edge_desirability / total_desirability

        return edge_probabilities

    def _get_edge_desirability(self, target_node: str) -> float:
        """
        Computes the desirability of an edge between the current node and a target node.

        Args:
            target_node (str): The target node for which to calculate desirability.

        Returns:
            float: The desirability of the edge.
        """
        edge_pheromones = self.graph_api.get_edge_pheromones(self.current_node, target_node)
        edge_cost = self.graph_api.get_edge_cost(self.current_node, target_node)
        return pheromone_operators.compute_edge_desirability(edge_pheromones, edge_cost, self.alpha, self.beta)

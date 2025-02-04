from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional

from MMAS import pheromone_operators
from Shared.cevrp import CEVRP
from Shared.graph_api import GraphApi
from Shared.path import Path


@dataclass
class Ant:
    graph_api: GraphApi
    source: str
    alpha: float = 0.7
    beta: float = 0.3
    evaporation_rate: float = 0.98
    visited_nodes: Set[str] = field(default_factory=set)
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
        """
        Initializes the ant's state after the dataclass constructor is called.
        """
        if not self.graph_api:
            raise ValueError("graph_api must be provided.")

        # Set the spawn node as the current and first node
        self.current_node = self.source
        self.path.nodes.append(self.source)

    def reached_destination(self) -> bool:
        """
        Checks if the ant has visited all required nodes in the graph.

        Returns:
            bool: True if the ant has visited all required nodes, otherwise False.
        """
        return len(self.visited_nodes) >= len(self.graph_api.graph.nodes)

    def route_construction(self) -> None:
        """
        Constructs routes for the ant using pheromone information and capacity constraints.
        This method is an alternative to take_step.
        """
        # Reset the ant's state
        self.paths = []
        self.path = Path()
        self.path.nodes.append(self.source)
        self.visited_nodes = set()
        self.limit_load_current_vehicle = 0
        self.vehicle_counter = 0
        self.path_cost = 0.0

        # Get the list of customers to visit
        customers = [node for node in self.graph_api.graph.nodes if node != self.source]
        remaining_customers = set(customers)

        while remaining_customers:
            # Filter feasible customers based on capacity constraint
            feasible_customers = [
                node for node in remaining_customers
                if self.graph_api.get_demand_node(node) <= self.cevrp.capacity - self.limit_load_current_vehicle
            ]

            # If no feasible customers, return to the depot
            if not feasible_customers:
                self.path.nodes.append(self.source)
                self.paths.append(self.path)
                self.path = Path()
                self.path.nodes.append(self.source)
                self.limit_load_current_vehicle = 0
                self.vehicle_counter += 1
                continue

            # Select the next node using roulette wheel selection
            next_node = self._choose_next_node_from_feasible(feasible_customers)

            # Update the ant's path and visited nodes
            self.path.nodes.append(next_node)
            self.visited_nodes.add(next_node)
            remaining_customers.remove(next_node)

            # Update the path cost and vehicle load
            edge_cost = self.calculate_edge_cost(next_node)
            self.path_cost += edge_cost
            self.path.path_cost += edge_cost
            self.limit_load_current_vehicle += self.graph_api.get_demand_node(next_node)

        # Finalize the last route by returning to the depot
        if len(self.path.nodes) > 1:  # Avoid adding empty paths
            self.path.nodes.append(self.source)
            self.paths.append(self.path)

    def _choose_next_node_from_feasible(self, feasible_customers: List[str]) -> str:
        """
        Chooses the next node from the list of feasible customers using roulette wheel selection.

        Args:
            feasible_customers (List[str]): List of feasible customers to visit.

        Returns:
            str: The next node to visit.
        """
        edge_probabilities = self._calculate_edge_probabilities_for_feasible(feasible_customers)
        return pheromone_operators.roulette_wheel_selection(edge_probabilities)

    def _calculate_edge_probabilities_for_feasible(self, feasible_customers: List[str]) -> Dict[str, float]:
        """
        Calculates the transition probabilities for feasible customers.

        Args:
            feasible_customers (List[str]): List of feasible customers to visit.

        Returns:
            Dict[str, float]: A dictionary mapping nodes to their transition probabilities.
        """
        edge_probabilities: Dict[str, float] = {}
        total_desirability = self._compute_all_edges_desirability_for_feasible(feasible_customers)

        for node in feasible_customers:
            edge_desirability = self._get_edge_desirability(node)
            edge_probabilities[node] = edge_desirability / total_desirability

        return edge_probabilities

    def _compute_all_edges_desirability_for_feasible(self, feasible_customers: List[str]) -> float:
        """
        Computes the denominator of the transition probability equation for feasible customers.

        Args:
            feasible_customers (List[str]): List of feasible customers to visit.

        Returns:
            float: The summation of all the outgoing edges (to feasible customers) from the current node.
        """
        total = 0.0
        for node in feasible_customers:
            edge_pheromones = self.graph_api.get_edge_pheromones(self.current_node, node)
            edge_cost = self.graph_api.get_edge_cost(self.current_node, node)
            total += pheromone_operators.compute_edge_desirability(edge_pheromones, edge_cost, self.alpha, self.beta)

        return total

    def take_step(self) -> None:
        """Compute and update the ant position"""

        # Pick the next node of the ant
        next_node = self._choose_next_node()

        # Update the ant's path and visited nodes
        self.path.nodes.append(next_node)
        self.visited_nodes.add(self.current_node)

        # Update the path cost
        edge_cost = self.calculate_edge_cost(next_node)
        self.path_cost += edge_cost
        self.path.path_cost += edge_cost

        if next_node == self.source:
            # If the next node is the source, finalize the current path and start a new one
            self.paths.append(self.path)
            self.path = Path()
            self.path.nodes.append(self.source)
            self.limit_load_current_vehicle = 0
            self.vehicle_counter += 1
        else:
            # Update the current node and the vehicle's load
            self.limit_load_current_vehicle += self.graph_api.get_demand_node(next_node)
            self.current_node = next_node

    def calculate_edge_cost(self, next_node: str) -> float:
        """
        Calculates the cost of the edge from the current node to the next node.

        Args:
            next_node (str): The next node to visit.

        Returns:
            float: The cost of the edge.
        """
        return self.graph_api.get_edge_cost(self.current_node, next_node)

    def _choose_next_node(self) -> str:
        """
        Chooses the next node to be visited by the ant using roulette wheel selection.

        Returns:
            str: The next node to visit.
        """
        unvisited_neighbors = self._get_unvisited_neighbors_with_demand()
        remaining_vehicle_cap = self.cevrp.capacity * (self.cevrp.vehicles - self.vehicle_counter - 1)
        total_neighbors_demand = self.graph_api.get_total_demand_of_neighbors(unvisited_neighbors)

        if total_neighbors_demand <= remaining_vehicle_cap or not unvisited_neighbors:
            unvisited_neighbors.append({'node': self.source, 'demand': 0})

        edge_probabilities = self._calculate_edge_probabilities(unvisited_neighbors)
        return pheromone_operators.roulette_wheel_selection(edge_probabilities)

    def _get_unvisited_neighbors_with_demand(self) -> List[Dict[str, int]]:
        """
        Returns a list of unvisited neighbors of the current node, along with each neighbor's demand.

        Returns:
            List[Dict[str, int]]: A list of dictionaries containing each unvisited neighbor and its demand.
        """
        unvisited_neighbors_with_demand = []
        neighbors_with_demand = self.graph_api.get_neighbors_with_demand(self.current_node)

        for neighbor_info in neighbors_with_demand:
            neighbor_node = neighbor_info['node']
            neighbor_demand = neighbor_info['demand']
            if (neighbor_node not in self.visited_nodes and
                    neighbor_demand <= self.cevrp.capacity - self.limit_load_current_vehicle):
                unvisited_neighbors_with_demand.append(neighbor_info)

        return unvisited_neighbors_with_demand

    def deposit_pheromones_on_paths(self) -> None:
        """
        Updates the pheromones along all the edges in the paths.
        """
        for path in self.paths:
            for i in range(len(path.nodes) - 1):
                u, v = path.nodes[i], path.nodes[i + 1]
                new_pheromone_value = pheromone_operators.calculate_pheromone_value(
                    self.evaporation_rate,
                    self.graph_api.get_edge_pheromones(u, v),
                    self.best_path_cost,
                    self.graph_api.get_length_graph()
                )
                self.graph_api.deposit_pheromones(u, v, new_pheromone_value)

    def _compute_all_edges_desirability(self, neighbors_with_demand: List[Dict[str, int]]) -> float:
        """
        Computes the denominator of the transition probability equation for the ant.

        Args:
            neighbors_with_demand (List[Dict[str, int]]): All unvisited neighbors of the current node.

        Returns:
            float: The summation of all the outgoing edges (to unvisited nodes) from the current node.
        """
        total = 0.0
        for neighbor in neighbors_with_demand:
            neighbor_node = str(neighbor['node'])
            edge_pheromones = self.graph_api.get_edge_pheromones(self.current_node, neighbor_node)
            edge_cost = self.graph_api.get_edge_cost(self.current_node, neighbor_node)
            total += pheromone_operators.compute_edge_desirability(edge_pheromones, edge_cost, self.alpha, self.beta)

        return total

    def _calculate_edge_probabilities(self, unvisited_neighbors: List[Dict[str, int]]) -> Dict[str, float]:
        """
        Calculates the transition probabilities of all edges from the current node.

        Args:
            unvisited_neighbors (List[Dict[str, int]]): A list of unvisited neighbors with demand.

        Returns:
            Dict[str, float]: A dictionary mapping nodes to their transition probabilities.
        """
        edge_probabilities: Dict[str, float] = {}
        total_desirability = self._compute_all_edges_desirability(unvisited_neighbors)

        for neighbor in unvisited_neighbors:
            node_identifier = str(neighbor['node'])
            edge_desirability = self._get_edge_desirability(node_identifier)
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
from dataclasses import dataclass
from typing import List, Dict
from itertools import cycle

from Shared.cevrp import CEVRP
from Shared.path import Path
from collections import defaultdict

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.colors as colors

@dataclass
class GraphApi:
    graph: nx.DiGraph

    def set_edge_pheromones(self, u: str, v: str, pheromone_amount: float) -> None:
        if self.graph.has_edge(u, v):
            self.graph.edges[u,v]['pheromones'] = pheromone_amount

    def get_edge_pheromones(self, u: str, v: str) -> float:
        if self.graph.has_edge(u, v):
            return self.graph[u][v].get("pheromones", 0.0)
        return 0.0

    def deposit_pheromones(self, u: str, v: str, pheromone_amount: float) -> None:
        if self.graph.has_edge(u, v):
            self.graph.edges[u,v]['pheromones'] = pheromone_amount

    def get_edge_cost(self, u: str, v: str) -> float:
        if self.graph.has_edge(u, v):
            return self.graph[u][v].get("cost", 0.0)
        return 0.0

    def get_all_nodes(self) -> List[str]:
        return list(self.graph.nodes)

    def get_total_demand(self) -> int:
        total_demand = 0
        for neighbor in self.graph.nodes:
            total_demand += self.graph.nodes[neighbor].get('demand', 0)
        return  total_demand

    def get_total_demand_path(self, nodes) -> int:
        total_demand = 0
        for node in nodes:
            demand = self.get_demand_node(node)
            total_demand +=demand
        return  total_demand

    def get_length_graph(self) -> int:
        return len(self.graph.nodes)

    def get_neighbors(self, node: str) -> List[str]:
        return list(self.graph.neighbors(node))

    def get_neighbors_with_demand(self, node: str) -> List[dict]:
        """Returns a list of neighbors for a given node, along with each neighbor's demand.

        Args:
            node (str): The node for which to find neighbors.

        Returns:
            List[dict]: A list of dictionaries containing neighbor nodes and their demand.
        """
        if node not in self.graph:
            return []

        neighbors_with_demand = []
        for neighbor in self.get_neighbors(node):
            demand = self.graph.nodes[neighbor].get('demand', 0)
            neighbors_with_demand.append({'node': neighbor, 'demand': demand})

        return neighbors_with_demand

    def get_demand_node(self, node: str | int) -> float:
        return self.graph.nodes[node].get('demand', 0)

    def calculate_segment_cost_with_insertion(self, u: str, node: str, v: str) -> float:
        """
        Calculates the incremental cost of inserting a node between two other nodes.

        :param u: The first node before the insertion point.
        :param node: The node to be inserted.
        :param v: The second node after the insertion point.
        :return: Incremental cost of inserting 'node' between 'u' and 'v'.
        """
        # Cost before insertion
        original_cost = self.get_edge_cost(u, v)

        # Cost after insertion
        insertion_cost = (
            self.get_edge_cost(u, node) +
            self.get_edge_cost(node, v)
        )

        # Incremental cost
        return insertion_cost - original_cost

    def visualize_graph(self, paths: List[Path], name: str) -> None:

        """Visualizes the graph with highlighted paths, costs in legend, and total cost in title.

        Features:
        - Curved overlapping edges for better visibility
        - Automatic total cost calculation
        - Unique colors for each path
        - Adaptive edge curvature for parallel routes
        """

        # Get node positions from graph attributes
        node_positions = nx.get_node_attributes(self.graph, "pos")
        if not node_positions:
            raise ValueError("Node positions missing. Ensure nodes have 'pos' attribute.")

        # Initialize figure with custom size
        plt.figure(figsize=(12, 12))

        # Calculate total cost and create formatted title
        total_cost = sum(path.path_cost for path in paths)
        plt.title(f"{name}\nTotal Cost: {total_cost:.2f}",
                  fontsize=16,
                  fontweight="bold",
                  pad=20)

        # Configure grid and axes
        plt.grid(visible=True, linestyle="--", linewidth=0.5, alpha=0.7)
        plt.axhline(0, color="black", linewidth=1)  # X-axis line
        plt.axvline(0, color="black", linewidth=1)  # Y-axis line
        plt.xlabel("X-axis", fontsize=14)
        plt.ylabel("Y-axis", fontsize=14)

        # Draw base graph elements
        nx.draw_networkx_nodes(self.graph, node_positions,
                               node_color="lightblue",
                               node_size=600)
        nx.draw_networkx_labels(self.graph, node_positions,
                                font_size=10)

        # Path visualization setup
        color_iterator = cycle(colors.TABLEAU_COLORS)
        legend_items = []
        edge_counts = defaultdict(int)  # Track edge usage for curvature

        # Draw each path with unique styling
        for idx, path in enumerate(paths):
            color = next(color_iterator)
            edges = list(zip(path.nodes, path.nodes[1:]))

            # Calculate curvature for overlapping edges
            connection_styles = []
            for u, v in edges:
                # Use sorted nodes to handle undirected graphs
                key = tuple(sorted((u, v)))
                count = edge_counts[key]
                rad = 0.3 * count  # Base curvature multiplier
                connection_styles.append(f"arc3,rad={rad}")
                edge_counts[key] += 1

            # Draw each edge individually with its specific connection style
            for edge, conn_style in zip(edges, connection_styles):
                nx.draw_networkx_edges(
                    self.graph, node_positions,
                    edgelist=[edge],
                    edge_color=color,
                    width=2,
                    style="solid",
                    connectionstyle=conn_style
                )

            legend_items.append((f"Path {idx + 1}: {path.path_cost:.2f}", color))

        # Create legend with custom handles
        legend_handles = [plt.Line2D([0], [0], color=c, lw=2) for _, c in legend_items]
        plt.legend(legend_handles, [label for label, _ in legend_items],
                   loc="upper right",
                   fontsize=9,
                   framealpha=0.9)

        # Set dynamic axis limits with padding
        x_vals, y_vals = zip(*node_positions.values())
        plt.xlim(min(x_vals) - 1, max(x_vals) + 1)
        plt.ylim(min(y_vals) - 1, max(y_vals) + 1)

        # Final rendering
        plt.tight_layout()
        plt.show()

    def calculate_path_cost(self, nodes: list[str]) -> float:
        """
        Calculates the total cost of a path based on the edges in the graph.
        :param nodes: List of nodes in the path.
        :return: The total cost of the path.
        """
        cost = 0.0
        for i in range(len(nodes) - 1):
            cost += self.get_edge_cost(nodes[i], nodes[i + 1])
        return cost

    def calculate_path_energy_consumption(self, nodes: list[str], energy_consumption:float) -> float:
        path_cost = self.calculate_path_cost(nodes)
        return path_cost * energy_consumption

    def calculate_edge_energy_consumption(self,  u: str, v: str, energy_consumption:float) -> float:
        edge_cost = self.get_edge_cost(u, v)
        return edge_cost * energy_consumption

    def calculate_minimum_stations(self, nodes: list[str], energy_consumption: float, energy_capacity: float) -> float:
        return (self.calculate_path_cost(nodes) * energy_consumption) / energy_capacity

    def calculate_max_energy_to_station(self, nodes:List[str], cevrp:CEVRP):
        """Calculates the maximum energy required for a route to reach the nearest charging station."""
        max_energy_needed = 0
        for node in nodes:
            for station in cevrp.charging_stations:
                energy_required = self.calculate_edge_energy_consumption(node, station, cevrp.energy_consumption)
                max_energy_needed = max(max_energy_needed, energy_required)
        return max_energy_needed

    @staticmethod
    def are_valid_paths(paths: List[Path]) -> bool:
        for path in paths:
            if len(path.nodes) <= 3:
                return False
        return True

    @staticmethod
    def calculate_paths_cost(paths: List[Path]) -> float:
        """Calculate the total cost of the provided paths."""
        return sum(path.path_cost for path in paths)

    @staticmethod
    def get_total_demand_of_neighbors(neighbors_with_demand: List[Dict[str, int]]) -> int:
        """Calculates and returns the total demand of a given list of neighbors.

        Args:
            neighbors_with_demand (List[Dict[str, int]]): A list of dictionaries containing each neighbor and its demand.

        Returns:
            int: The sum of the demands of all the given neighbors.
        """
        return sum(neighbor_info['demand'] for neighbor_info in neighbors_with_demand)
from dataclasses import dataclass
from typing import List, Dict
from itertools import cycle
from Shared.path import Path

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
            total_demand += self.get_demand_node(node)
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
        for neighbor in self.graph.neighbors(node):
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

    def visualize_graph(self, paths: List[Path], name:str) -> None:

        """Visualizes the graph with paths highlighted in unique colors, costs in the legend, and a title."""

        # Get node positions
        node_positions = nx.get_node_attributes(self.graph, "pos")
        if not node_positions:
            raise ValueError("Node positions are missing in the graph. Ensure nodes have the 'pos' attribute.")

        # Configure the plot
        plt.figure(figsize=(12, 12))  # Adjusted size to improve visualization
        plt.title(name, fontsize=16, fontweight="bold")  # Add title
        plt.grid(visible=True, which="both", color="gray", linestyle="--", linewidth=0.5, alpha=0.7)
        plt.gca().set_axisbelow(True)  # Ensure grid is below other elements
        plt.axhline(0, color="black", linewidth=1)  # X-axis
        plt.axvline(0, color="black", linewidth=1)  # Y-axis
        plt.xlabel("X-axis", fontsize=14)
        plt.ylabel("Y-axis", fontsize=14)

        # Draw nodes
        nx.draw_networkx_nodes(self.graph, node_positions, node_color="lightblue", node_size=600)
        nx.draw_networkx_labels(self.graph, node_positions, font_size=10, font_color="black")

        # Iterate through paths and draw each with a unique color
        color_iterator = cycle(colors.TABLEAU_COLORS.values())  # Create a cyclic color iterator
        legend_items = []  # Store legend items as labels and color handles
        for i, path in enumerate(paths):
            color = next(color_iterator)
            edges = list(zip(path.nodes, path.nodes[1:]))
            nx.draw_networkx_edges(self.graph, node_positions, edgelist=edges, edge_color=color, width=3)
            legend_items.append((f"Path {i + 1}: Cost {path.path_cost:.2f}", color))  # Add path to legend

        # Add Legend at the top-right
        legend_labels, legend_colors = zip(*legend_items)  # Separate labels and colors
        legend_handles = [plt.Line2D([0], [0], color=color, lw=3) for color in legend_colors]  # Legend handles
        plt.legend(legend_handles, legend_labels, loc="upper right", fontsize=10, frameon=True)

        # Set axis limits for better visualization
        x_values, y_values = zip(*node_positions.values())
        plt.xlim(min(x_values) - 1, max(x_values) + 1)
        plt.ylim(min(y_values) - 1, max(y_values) + 1)

        # Show the graph
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
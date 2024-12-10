from dataclasses import dataclass
from typing import List, Dict
from itertools import cycle

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.colors as colors



@dataclass
class GraphApi:
    graph: nx.DiGraph
    evaporation_rate: float

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

    @staticmethod
    def get_total_demand_of_neighbors(neighbors_with_demand: List[Dict[str, int]]) -> int:
        """Calculates and returns the total demand of a given list of neighbors.

        Args:
            neighbors_with_demand (List[Dict[str, int]]): A list of dictionaries containing each neighbor and its demand.

        Returns:
            int: The sum of the demands of all the given neighbors.
        """
        return sum(neighbor_info['demand'] for neighbor_info in neighbors_with_demand)

    def get_demand_node(self, node: str | int) -> float:
        return self.graph.nodes[node].get('demand', 0)

    def visualize_graph(self, shortest_path: List[str]) -> None:
        """Visualizes the graph with a grid background and labeled axes.

        Handles repetitive nodes in the shortest path, ensuring subpaths close at the depot.

        Args:
            shortest_path (List[str]): The nodes in the shortest path.
        """

        # Extract node positions from the graph
        node_positions = nx.get_node_attributes(self.graph, "pos")

        # Validate the positions
        if not node_positions:
            raise ValueError("Node positions are missing in the graph. Ensure nodes have a 'pos' attribute.")

        # Adjust the figure size
        plt.figure(figsize=(12, 12))

        # Add grid and axis lines
        plt.grid(visible=True, which="both", color="gray", linestyle="--", linewidth=0.5, alpha=0.7)
        plt.gca().set_axisbelow(True)  # Draw grid behind other elements
        plt.axhline(0, color="black", linewidth=1)  # X-axis
        plt.axvline(0, color="black", linewidth=1)  # Y-axis

        # Label axes
        plt.xlabel("X-axis", fontsize=14)
        plt.ylabel("Y-axis", fontsize=14)

        # Separate the path into subpaths that start and end with "1"
        paths = []
        current_path = []

        for node in shortest_path:
            current_path.append(node)
            if node == "1" and len(current_path) > 1:  # Close the sub path when reaching "1"
                paths.append(current_path)
                current_path = [node]  # Start a new sub path with the current "1"

        if len(current_path) > 1:  # Ensure the last sub path is added if it doesn't end with "1"
            paths.append(current_path)

        # Draw nodes
        nodes_in_path = set(shortest_path)
        nx.draw_networkx_nodes(self.graph, node_positions, nodelist=nodes_in_path, node_color="lightblue",
                               node_size=600)

        # Use a color map from matplotlib
        color_map = list(colors.TABLEAU_COLORS.values())  # Get a list of named colors from Tableau color set
        color_cycle = cycle(color_map)  # Cycle through the colors

        # Draw edges for each sub path in distinguishable colors
        for path in paths:
            color = next(color_cycle)
            edges = list(zip(path, path[1:]))
            nx.draw_networkx_edges(
                self.graph,
                node_positions,
                edgelist=edges,
                edge_color=color,
                width=3,
            )

        # Add labels for the nodes
        nx.draw_networkx_labels(self.graph, node_positions, font_size=10, font_color="black")

        # Set limits for better visualization
        x_values, y_values = zip(*node_positions.values())
        plt.xlim(min(x_values) - 1, max(x_values) + 1)
        plt.ylim(min(y_values) - 1, max(y_values) + 1)

        # Show the plot
        plt.gca().margins(0.1)
        plt.axis("on")  # Keep the axes visible
        plt.tight_layout()
        plt.show()

    def show_graph(self):
        print(f"Number of nodes: {self.graph.number_of_nodes()}")
        print(f"Number of edges: {self.graph.number_of_edges()}")
        print("\nSome edges of the graph:")
        for i, (u, v, data) in enumerate(self.graph.edges(data=True)):
            print(f"Edge from {u} to {v} with cost {data['cost']:.2f}")
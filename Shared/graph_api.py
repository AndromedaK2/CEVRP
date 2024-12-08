from dataclasses import dataclass
from typing import List, Dict
import networkx as nx
import matplotlib.pyplot as plt
from itertools import cycle


@dataclass
class GraphApi:
    graph: nx.DiGraph
    evaporation_rate: float

    def set_edge_pheromones(self, u: str, v: str, pheromone_value: float) -> None:
        if self.graph.has_edge(u, v):
            self.graph[u][v]["pheromones"] = pheromone_value
        else:
            raise ValueError(f"No existe una arista entre {u} y {v}. No se puede asignar el valor de feromonas.")

    def get_edge_pheromones(self, u: str, v: str) -> float:
        if self.graph.has_edge(u, v):
            return self.graph[u][v].get("pheromones", 0.0)
        return 0.0

    def deposit_pheromones(self, u: str, v: str, pheromone_amount: float) -> None:
        if self.graph.has_edge(u, v):
            self.graph[u][v]["pheromones"] = pheromone_amount

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

        Highlights the shortest_path with distinguishable colors.

        Args:
            shortest_path (List[str]): The nodes in the shortest path.
        """

        # Extract node positions from the graph
        node_positions = nx.get_node_attributes(self.graph, "pos")

        # Validate the positions
        if not node_positions:
            raise ValueError("Node positions are missing in the graph. Ensure nodes have a 'pos' attribute.")

        # Adjust the figure size
        plt.figure(figsize=(12, 12))  # Set a square figure for better alignment

        # Add grid and axis lines
        plt.grid(visible=True, which="both", color="gray", linestyle="--", linewidth=0.5, alpha=0.7)
        plt.gca().set_axisbelow(True)  # Draw grid behind other elements
        plt.axhline(0, color="black", linewidth=1)  # X-axis
        plt.axvline(0, color="black", linewidth=1)  # Y-axis

        # Label axes
        plt.xlabel("X-axis", fontsize=14)
        plt.ylabel("Y-axis", fontsize=14)

        # Draw nodes
        nodes_in_path = set(shortest_path)
        nx.draw_networkx_nodes(self.graph, node_positions, nodelist=nodes_in_path, node_color="lightblue",
                               node_size=600)

        # Get a cycle of distinguishable colors
        color_cycle = cycle(plt.cm.tab10.colors)

        # Draw edges in the shortest path
        for path_start, path_end in zip(shortest_path[:-1], shortest_path[1:]):
            color = next(color_cycle)
            nx.draw_networkx_edges(
                self.graph,
                node_positions,
                edgelist=[(path_start, path_end)],
                edge_color=color,
                width=3,
            )

        # Add labels
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

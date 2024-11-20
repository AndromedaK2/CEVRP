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
            return self.graph[u][v].get("pheromones", 0.0)  # Devuelve `0.0` si no hay feromonas definidas
        else:
            raise ValueError(f"No existe una arista entre {u} y {v}")

    def deposit_pheromones(self, u: str, v: str, pheromone_amount: float) -> None:
        self.graph[u][v]["pheromones"] += max(
            (1 - self.evaporation_rate) + pheromone_amount, 1e-13
        )

    def get_edge_cost(self, u: str, v: str) -> float:
        if self.graph.has_edge(u, v):
            return self.graph[u][v].get("cost", 0.0)
        else:
            raise ValueError(f"No existe una arista entre {u} y {v}")

    def get_all_nodes(self) -> List[str]:
        return list(self.graph.nodes)

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
            demand = self.graph.nodes[neighbor].get('demand',0)
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

    def get_demand_node(self, node: str | int ) -> float:
        return self.graph.nodes[node].get('demand',0)

    def visualize_graph(self, shortest_path: List[str]) -> None:
        """Visualizes only the paths present in the shortest_path, highlighted with distinguishable colors.

        Args:
            shortest_path (List[str]): The nodes in the shortest path.
        """

        # Define the layout for the graph
        pos = nx.spring_layout(self.graph, seed=2)  # Change layout if needed

        # Adjust the figure size
        plt.figure(figsize=(30, 15))  # Increase figure size for better visibility

        # Draw only the nodes involved in the shortest path (remove others)
        nodes_in_path = set(shortest_path)
        nx.draw_networkx_nodes(self.graph, pos, nodelist=nodes_in_path, node_color="lightblue", node_size=1000)

        # Get a cycle of distinguishable colors from matplotlib's "tab10" palette
        color_cycle = cycle(plt.cm.tab10.colors)

        # Split the shortest_path into separate subpaths when consecutive "1"s are found
        paths = []
        current_path = []

        for node in shortest_path:
            if node == "1" and current_path and current_path[-1] == "1":
                # When a consecutive "1" is found, start a new subpath
                paths.append(current_path)
                current_path = [node]  # Start a new subpath with the current "1"
            else:
                current_path.append(node)

        # Append the last path
        if current_path:
            paths.append(current_path)

        # Draw only the edges present in the shortest path
        for path in paths:
            color = next(color_cycle)  # Get the next color in the cycle
            nx.draw_networkx_edges(
                self.graph,
                pos,
                edgelist=list(zip(path, path[1:])),
                edge_color=color,  # Use the color from the tab10 palette
                width=4,
            )

        # Add node labels for the nodes in the shortest path
        # Create a dictionary of node labels only for the nodes in the path
        labels = {node: node for node in nodes_in_path}
        nx.draw_networkx_labels(self.graph, pos, labels=labels, font_size=14, font_color="black")

        # Display the graph
        plt.gca().margins(0.1)
        plt.axis("off")
        plt.tight_layout()
        plt.show()
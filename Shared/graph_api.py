import operator
import os
from dataclasses import dataclass
from typing import List, Dict
from itertools import cycle

from Shared.experiment import config
from Shared.path import Path
from collections import defaultdict, deque

import networkx as nx
import plotly.graph_objects as go

@dataclass
class GraphApi:
    graph: nx.DiGraph

    def __post_init__(self):
        self.len_graph = len(self.graph.nodes)

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

    def get_total_demand_path(self, nodes) -> int:
        get_demand = self.get_demand_node
        return sum(map(get_demand, nodes))

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

        nodes_data = self.graph.nodes
        return [
            {'node': neighbor, 'demand': nodes_data[neighbor].get('demand', 0)}
            for neighbor in self.get_neighbors(node)
        ]

    def get_demand_node(self, node: str | int) -> float:
        return self.graph.nodes[node].get('demand', 0)

    def get_node_coordinates(self, node: str) -> tuple[float, float] | None:
        node_positions = nx.get_node_attributes(self.graph, "pos")
        return node_positions.get(node)

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

    def visualize_graph(self, paths: List[Path], charging_stations, name: str, directory_path="") -> None:
        """Enhanced interactive visualization of the graph using Plotly with custom styling."""

        # Get node positions
        node_positions = nx.get_node_attributes(self.graph, "pos")
        if not node_positions:
            raise ValueError("Node positions missing. Ensure nodes have 'pos' attribute.")

        # Initialize Plotly figure
        fig = go.Figure()

        # Identify special nodes
        depot_node = config.default_source_node
        all_nodes = node_positions.keys()
        regular_nodes = [n for n in all_nodes if n != depot_node and n not in charging_stations]
        charging_nodes = [n for n in all_nodes if n in charging_stations]
        depot_nodes = [depot_node] if depot_node in all_nodes else []

        # Draw nodes with different markers
        def add_nodes(node_list, color, symbol, name, size=12):
            if node_list:
                positions = [node_positions[n] for n in node_list if n in node_positions]
                if positions:
                    x, y = zip(*positions)
                    fig.add_trace(go.Scatter(x=x, y=y, mode='markers+text', text=[str(n) for n in node_list],
                                             textposition='top center',
                                             marker=dict(size=size, color=color, symbol=symbol,
                                                         line=dict(width=2, color='black')),
                                             name=name))

        add_nodes(regular_nodes, 'lightblue', 'circle', 'Customers', size=14)
        add_nodes(charging_nodes, 'red', 'triangle-up', 'Charging Stations', size=16)
        add_nodes(depot_nodes, 'green', 'square', 'Depot', size=18)

        # Path visualization with curved edges
        color_iterator = cycle(['blue', 'purple', 'orange', 'cyan', 'magenta'])
        edge_counts = defaultdict(int)

        for idx, path in enumerate(paths):
            color = next(color_iterator)
            edges = list(zip(path.nodes, path.nodes[1:]))

            x_edges, y_edges = [], []
            for u, v in edges:
                x_edges += [node_positions[u][0], node_positions[v][0], None]
                y_edges += [node_positions[u][1], node_positions[v][1], None]

            fig.add_trace(
                go.Scatter(x=x_edges, y=y_edges, mode='lines',
                           line=dict(color=color, width=3, dash='solid'),
                           opacity=0.8,
                           name=f'Path {idx + 1}'))

        total_cost = sum(path.path_cost for path in paths)

        # Set layout with enhanced aesthetics
        fig.update_layout(title=f"{name} - Total Cost: {total_cost:.2f}",
                          xaxis=dict(title='X-axis', showgrid=True, zeroline=False),
                          yaxis=dict(title='Y-axis', showgrid=True, zeroline=False),
                          plot_bgcolor='rgba(240,240,240,0.9)',
                          showlegend=True)
        final_path = f"./{directory_path}/{name}-{total_cost}.html"
        os.makedirs(os.path.dirname(final_path), exist_ok=True)
        fig.write_html(final_path)
        fig.show()

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

    def is_path_connected(self, nodes: List[str]) -> bool:
        """
        Checks if all nodes in the given path remain connected after a modification.

        :param nodes: The list of nodes (as strings) representing the path.
        :return: True if the path is fully connected, False otherwise.
        """
        if not nodes:
            return False  # An empty path is not connected

        visited = set()
        queue = deque([nodes[0]])  # Start BFS from the first node

        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)

            # Check all distinct neighbors within the path
            for neighbor in nodes:
                if neighbor != current and neighbor not in visited and self.has_edge(current, neighbor):
                    queue.append(neighbor)

        # Path is connected if all nodes have been visited
        return len(visited) == len(set(nodes))  # Ensures all unique nodes were reachable

    def has_edge(self, u: str, v: str) -> bool:
        """
        Checks if there is a direct edge between two nodes in the graph.

        :param u: The first node.
        :param v: The second node.
        :return: True if an edge exists between u and v, False otherwise.
        """
        return self.graph.has_edge(u, v)

    def is_feasible(self,route1_nodes: List[str], route2_nodes: List[str], capacity:int) -> bool:
        """
        Checks if the swap maintains energy and capacity feasibility.

        Args:
            route1_nodes (List[str]): First modified route.
            route2_nodes (List[str]): Second modified route.

        Returns:
            bool: True if the swap is feasible, False otherwise.
            :param route2_nodes:
            :param route1_nodes:
            :param capacity:
        """
        new_demand1 = self.get_total_demand_path(route1_nodes)
        new_demand2 = self.get_total_demand_path(route2_nodes)

        return new_demand1 <= capacity and new_demand2 <= capacity

    @staticmethod
    def calculate_paths_cost(paths: List[Path]) -> float:
        """Calculate the total cost of the provided paths."""
        return sum(map(operator.attrgetter('path_cost'), paths))

    @staticmethod
    def get_total_demand_of_neighbors(neighbors_with_demand: List[Dict[str, int]]) -> int:
        """Calculates and returns the total demand of a given list of neighbors.

        Args:
            neighbors_with_demand (List[Dict[str, int]]): A list of dictionaries containing each neighbor and its demand.

        Returns:
            int: The sum of the demands of all the given neighbors.
        """
        return sum(map(operator.itemgetter('demand'), neighbors_with_demand))
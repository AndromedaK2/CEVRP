from dataclasses import dataclass
from typing import Optional

import networkx as nx
import numpy as np
import pandas as pd

@dataclass
class CoordinatesManager:
    data: np.ndarray
    distances: Optional[np.ndarray] = None
    graph: nx.DiGraph = nx.DiGraph()

    def __post_init__(self):
        self.nodes = pd.DataFrame(self.data, columns=['ID', 'X', 'Y', 'Demand'])

    def compute_distances(self):
        coordinates = self.nodes[['X', 'Y']].values
        self.distances = np.linalg.norm(coordinates[:, np.newaxis] - coordinates, axis=2)

    def get_distance_matrix(self):
        if self.distances is not None:
            return pd.DataFrame(self.distances, index=self.nodes['ID'], columns=self.nodes['ID'])
        else:
            raise ValueError("Distances have not been calculated. Please call compute_distances first.")

    def build_graph(self):
        def add_nodes_to_graph(graph, nodes):
            for _, row in nodes.iterrows():
                demand = row['Demand'] if pd.notnull(row['Demand']) else 0
                graph.add_node(str(row['ID']), pos=(row['X'], row['Y']), demand=demand)

        g = nx.DiGraph()
        add_nodes_to_graph(g, self.nodes)

        distance_matrix = self.get_distance_matrix()
        for i in distance_matrix.index:
            for j in distance_matrix.columns:
                if i != j:  # avoid auto-loops
                    g.add_edge(str(i), str(j), cost=distance_matrix.loc[i, j])

        self.graph = g
        return g




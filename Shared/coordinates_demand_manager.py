from dataclasses import dataclass
from typing import Optional

import networkx as nx
import numpy as np
import pandas as pd

@dataclass
class CoordinatesDemandManager:
    data: np.ndarray
    distances: Optional[np.ndarray] = None
    graph = nx.DiGraph()

    def __post_init__(self):
        self.cities = pd.DataFrame(self.data, columns=['ID', 'X', 'Y', 'Demand'])

    def calculate_distances(self):
        coords = self.cities[['X', 'Y']].values
        self.distances = np.linalg.norm(coords[:, np.newaxis] - coords, axis=2)

    def get_distances(self):
        if self.distances is not None:
            return pd.DataFrame(self.distances, index=self.cities['ID'], columns=self.cities['ID'])
        else:
            raise ValueError("Distances have not been calculated. Call calculate_distances first.")

    def create_graph_from_manager(self):
        g = nx.DiGraph()

        for _, row in self.cities.iterrows():
            demand = row['Demand'] if pd.notnull(row['Demand']) else 0
            g.add_node(str(row['ID']), pos=(row['X'], row['Y']), demand=demand)

        distances = self.get_distances()
        for i in distances.index:
            for j in distances.columns:
                if i != j:  # auto-loops
                    g.add_edge(str(i), str(j), cost=distances.loc[i, j])
        self.graph = g
        return g




from dataclasses import dataclass
from typing import Optional

import networkx as nx
import numpy as np
import pandas as pd

@dataclass
class CoordinatesDemandManager:
    data: np.ndarray
    distances: Optional[np.ndarray] = None

    def __post_init__(self):
        self.cities = pd.DataFrame(self.data, columns=['ID', 'X', 'Y', 'Demand'])

    def calculate_distances(self):
        coords = self.cities[['X', 'Y']].values
        self.distances = np.linalg.norm(coords[:, np.newaxis] - coords, axis=2)

    def get_distances(self):
        if self.distances is not None:
            return pd.DataFrame(self.distances, index=self.cities['ID'], columns=self.cities['ID'])
        else:
            raise ValueError("Las distancias no han sido calculadas. Llama a calculate_distances primero.")

    def create_graph_from_manager(self):
        g = nx.DiGraph()

        for _, row in self.cities.iterrows():
            g.add_node(int(row['ID']), pos=(row['X'], row['Y']), demand=row['Demand'])

        distances = self.get_distances()
        for i in distances.index:
            for j in distances.columns:
                if i != j:  # auto-bucles
                    g.add_edge(str(i), str(j), cost=distances.loc[i, j])

        return g

    def show_graph(G):
        print(f"Número de nodos: {G.number_of_nodes()}")
        print(f"Número de aristas: {G.number_of_edges()}")
        print("\nAlgunas aristas del grafo:")
        for i, (u, v, data) in enumerate(G.edges(data=True)):
            print(f"Arista de {u} a {v} con costo {data['cost']:.2f}")

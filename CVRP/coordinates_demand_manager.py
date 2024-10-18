from dataclasses import dataclass
from typing import Optional
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

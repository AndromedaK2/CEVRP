import copy
from typing import List

from Shared.cevrp import CEVRP
from Shared.graph_api import GraphApi
from Shared.path import Path

class CevrpState:
    def __init__(self, paths: list[Path], unassigned=None, graph_api:GraphApi=None,  cevrp:CEVRP=None):
        """
        Initializes a CevrpState object.

        :param paths: List of Path objects representing the current routes.
        :param unassigned: List of unassigned nodes (default is an empty list).
        :param graph_api: An instance of GraphApi for accessing graph-related methods.
        """
        self.paths = paths
        self.unassigned = unassigned if unassigned is not None else []
        self.graph_api = graph_api  # Store the graph_api instance
        self.cevrp = cevrp

    def objective(self):
        """
        Computes the total route costs.
        """
        return self.get_path_cost()

    @property
    def cost(self):
        """
        Alias for objective method. Used for plotting.
        """
        return self.objective()

    def copy(self) -> "CevrpState":
        """Creates a deep copy of the CevrpState instance."""
        return CevrpState(
            paths=[path.copy() for path in self.paths],
            unassigned=self.unassigned.copy(),
            graph_api=self.graph_api,  # Assuming graph_api is immutable or shared
            cevrp=self.cevrp  # Assuming cevrp is immutable or shared
        )

    def get_path_cost(self):
        """
        Calculates the total cost of all routes.

        :return: Total cost of all routes.
        """
        if self.graph_api is None:
            raise ValueError("graph_api instance is required to calculate path cost.")
        return self.graph_api.calculate_paths_cost(self.paths)

    def get_path_energy_consumption(self, nodes:List[str]):
        path_energy_consumption = self.graph_api.calculate_path_energy_consumption(nodes, self.cevrp.energy_consumption)
        return path_energy_consumption

    def get_edge_energy_consumption(self, i:str, j:str):
        edge_energy_consumption = self.graph_api.calculate_edge_energy_consumption(i,j, self.cevrp.energy_consumption)
        return edge_energy_consumption

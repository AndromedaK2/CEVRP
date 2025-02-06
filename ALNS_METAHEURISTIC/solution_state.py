import copy

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

    def copy(self):
        """Creates a duplicate of the current state."""
        # Make a deep copy of paths and a shallow copy of unassigned
        paths_copy = copy.deepcopy(self.paths)
        unassigned_copy = self.unassigned.copy()
        return CevrpState(paths_copy, unassigned_copy, self.graph_api)

    def get_path_cost(self):
        """
        Calculates the total cost of all routes.

        :return: Total cost of all routes.
        """
        if self.graph_api is None:
            raise ValueError("graph_api instance is required to calculate path cost.")
        return self.graph_api.calculate_paths_cost(self.paths)

    def get_path_energy_consumption(self, i:int):
        path_energy_consumption = self.graph_api.calculate_path_energy_consumption(self.paths[i].nodes, self.cevrp.energy_consumption)
        return path_energy_consumption

    def get_edge_energy_consumption(self, i:str, j:str):
        edge_energy_consumption = self.graph_api.calculate_edge_energy_consumption(i,j, self.cevrp.energy_consumption)
        return edge_energy_consumption

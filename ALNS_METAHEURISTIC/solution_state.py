import copy
from typing import List
from Shared.cevrp import CEVRP
from Shared.graph_api import GraphApi
from Shared.path import Path

class CevrpState:

    _visualization: bool = False

    def __init__(self, paths: list[Path], unassigned=None, graph_api: GraphApi = None,
                 cevrp: CEVRP = None, previous_state: "CevrpState" = None, visualization=False):
        """
        Initializes a CevrpState object.

        :param paths: List of Path objects representing the current routes.
        :param unassigned: List of unassigned nodes (default is an empty list).
        :param graph_api: An instance of GraphApi for accessing graph-related methods.
        :param cevrp: An instance of CEVRP for vehicle routing constraints.
        :param previous_state: A stored previous state before modifications.
        """
        self.paths = paths
        self.unassigned = unassigned if unassigned is not None else []
        self.graph_api = graph_api  # Store the graph_api instance
        self.cevrp = cevrp
        self.previous_state = previous_state  # Store previous state before modifications
        self.visualization = visualization


    def objective(self):
        """
        Computes the total route costs.
        """
        return self.get_paths_cost()

    @property
    def cost(self):
        """
        Alias for objective method. Used for plotting.
        """
        return self.objective()

    @property
    def visualization(self):
        return self._visualization

    @visualization.setter
    def visualization(self, value):
        self._visualization = value

    def copy(self) -> "CevrpState":
        """Creates a deep copy of the CevrpState instance."""
        return CevrpState(
            paths=[path.copy() for path in self.paths],
            unassigned=copy.deepcopy(self.unassigned),
            graph_api=self.graph_api,  # Assuming graph_api is immutable or shared
            cevrp=self.cevrp,  # Assuming cevrp is immutable or shared
            previous_state=self.previous_state,  # Preserve previous state in copy
            visualization=self.visualization,
        )

    def get_paths_cost(self):
        """
        Calculates the total cost of all routes.

        :return: Total cost of all routes.
        """
        if self.graph_api is None:
            raise ValueError("graph_api instance is required to calculate path cost.")
        return self.graph_api.calculate_paths_cost(self.paths)

    def get_path_energy_consumption(self, nodes: List[str]):
        return self.graph_api.calculate_path_energy_consumption(nodes, self.cevrp.energy_consumption)

    def get_edge_energy_consumption(self, i: str, j: str):
        return self.graph_api.calculate_edge_energy_consumption(i, j, self.cevrp.energy_consumption)

    def calculate_path_energy(self, nodes, charging_stations = None):
        """Calculates total energy usage for a path with resets at charging stations."""
        stations = set(charging_stations or self.cevrp.charging_stations)
        get_energy = self.get_edge_energy_consumption
        energy = 0

        for prev, curr in zip(nodes, nodes[1:]):
            energy = get_energy(prev, curr) if prev in stations else energy + get_energy(prev, curr)
        return energy

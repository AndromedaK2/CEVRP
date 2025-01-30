import copy
from typing import List, Optional

from Shared import graph_api
from Shared.path import Path


class CevrpState:
    def __init__(self, paths: List[Path], unassigned: Optional[List] = None):
        """
        Initializes a CevrpState object.

        :param paths: List of Path objects representing the current routes.
        :param unassigned: List of unassigned nodes (default is an empty list).
        """
        self.paths = paths
        self.unassigned = unassigned if unassigned is not None else []

    def objective(self) -> float:
        """
        Computes the total route costs.

        :return: Total cost of all routes.
        """
        return self.get_path_cost()

    @property
    def cost(self) -> float:
        """
        Alias for the objective method. Used for plotting.

        :return: Total cost of all routes.
        """
        return self.objective()

    def copy(self) -> 'CevrpState':
        """
        Creates a duplicate of the current state.

        :return: A new CevrpState object with copied paths and unassigned nodes.
        """
        # Make a deep copy of paths and a shallow copy of unassigned
        paths_copy = [copy.deepcopy(path) for path in self.paths]
        unassigned_copy = self.unassigned.copy()
        return CevrpState(paths_copy, unassigned_copy)

    def get_path_cost(self) -> float:
        """
        Calculates the total cost of all routes.

        :return: Total cost of all routes.
        """
        total_cost = 0  # Accumulate the total cost of all routes

        # Iterate over each Path object in the list of paths
        for path in self.paths:
            # Access nodes within the current Path
            nodes = path.nodes

            # Calculate the cost for the edges in the current path
            for i in range(len(nodes) - 1):
                total_cost += graph_api.GraphApi.get_edge_cost(nodes[i], nodes[i + 1])

        return total_cost  # Return the total cost of all routes
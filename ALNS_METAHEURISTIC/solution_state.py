import copy

from Shared import graph_api
from Shared.path import Path


class CevrpState:
    def __init__(self, paths: list[Path],  unassigned=None):
        self.paths = paths
        self.unassigned = unassigned if unassigned is not None else []

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
        # Makes a deep copy of 'routes' and a shallow copy of 'unassigned'
        routes_copy = copy.deepcopy(self.paths)
        unassigned_copy = self.unassigned.copy()
        return CevrpState(routes_copy, unassigned_copy)

    def get_path_cost(self):
        total_cost = 0  # Accumulate the total cost of all routes

        # Iterate over each Path object in the list of paths
        for path in self.paths:
            # Access nodes within the current Path
            nodes = path.nodes

            # Calculate the cost for the edges in the current path
            for i in range(len(nodes) - 1):
                total_cost += graph_api.GraphApi.get_edge_cost(nodes[i], nodes[i + 1])

        return total_cost  # Return the total cost of all routes

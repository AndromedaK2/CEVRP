import copy

from Shared.path import Path


class CevrpState:
    def __init__(self, paths: list[Path], unassigned=None, graph_api=None):
        """
        Initializes a CevrpState object.

        :param paths: List of Path objects representing the current routes.
        :param unassigned: List of unassigned nodes (default is an empty list).
        :param graph_api: An instance of GraphApi for accessing graph-related methods.
        """
        self.paths = paths
        self.unassigned = unassigned if unassigned is not None else []
        self.graph_api = graph_api  # Store the graph_api instance

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

        total_cost = 0  # Accumulate the total cost of all routes

        # Iterate over each Path object in the list of paths
        for path in self.paths:
            # Access nodes within the current Path
            nodes = path.nodes

            # Calculate the cost for the edges in the current path
            for i in range(len(nodes) - 1):
                total_cost += self.graph_api.get_edge_cost(nodes[i], nodes[i + 1])

        return total_cost  # Return the total cost of all routes
import random
from ALNS_METAHEURISTIC.solution_state import CevrpState
from Shared.path import Path

def calculate_path_cost(graph, nodes: list[str]) -> float:
    """
    Calculates the total cost of a path based on the edges in the graph.

    :param graph: The graph object with the method get_edge_cost.
    :param nodes: List of nodes in the path.
    :return: The total cost of the path.
    """
    cost = 0.0
    for i in range(len(nodes) - 1):
        cost += graph.get_edge_cost(nodes[i], nodes[i + 1])
    return cost

def random_destroy(graph,paths: list[Path], seed: int = None) -> CevrpState:
    """
    Randomly destroys two pairs of segments from the given paths.

    :param paths: List of Path objects representing the current routes.
    :param graph: The graph object with the method get_edge_cost.
    :param seed: Optional seed for reproducibility of random behavior.
    :return: A new CevrpState object with updated paths and unassigned nodes.
    :raises ValueError: If there are fewer than two paths or paths with insufficient nodes.
    """
    if seed is not None:
        random.seed(seed)

    if len(paths) < 2:
        raise ValueError("At least two paths are required to perform destruction.")

    # Make a deep copy of the paths to avoid modifying the original ones
    paths_copy = [path.copy() for path in paths]

    # Select two different paths randomly
    path_indices = random.sample(range(len(paths_copy)), 2)
    selected_paths = [paths_copy[i] for i in path_indices]

    # List to store unassigned nodes
    unassigned = []

    for path in selected_paths:
        if len(path.nodes) < 4:
            raise ValueError(f"Path {path} must have at least four nodes to destroy two segments.")

        # Randomly select two non-adjacent indices for the segments
        while True:
            segment_indices = sorted(random.sample(range(1, len(path.nodes) - 1), 2))
            if abs(segment_indices[1] - segment_indices[0]) > 1:
                break

        # Remove the segments and add to unassigned nodes
        for index in reversed(segment_indices):  # Reverse to avoid index shifting
            unassigned.append(path.nodes.pop(index))

        # Recalculate the path cost using the graph
        path.path_cost = calculate_path_cost(graph, path.nodes)

    # Create the new CevrpState
    return CevrpState(paths_copy, unassigned)

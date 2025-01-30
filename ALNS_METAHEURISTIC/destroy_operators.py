import random
from typing import Optional
from ALNS_METAHEURISTIC.solution_state import CevrpState


def random_destroy(state: CevrpState, rnd_state: Optional[random.Random] = None) -> CevrpState:
    """
    Randomly destroys two pairs of segments from the given paths.

    :param state: Current solution state (CevrpState).
    :param rnd_state: Random number generator state (optional).
    :return: A new CevrpState object with updated paths and unassigned nodes.
    :raises ValueError: If there are fewer than two paths or paths with insufficient nodes.
    """
    if rnd_state is not None:
        random.setstate(rnd_state.getstate())

    paths = state.paths

    if len(paths) < 2:
        raise ValueError("At least two paths are required to perform destruction.")

    # Make a deep copy of the paths to avoid modifying the original ones
    paths_copy = [path.copy() for path in paths]

    # Select two different paths randomly
    path_indices = random.sample(range(len(paths_copy)), 2)
    selected_paths = [paths_copy[i] for i in path_indices]

    # List to store unassigned nodes
    unassigned = state.unassigned.copy()

    for path in selected_paths:
        if len(path.nodes) < 4:
            raise ValueError(f"Path {path} must have at least four nodes to destroy two segments.")

        # Randomly select two non-adjacent indices for the segments
        while True:
            nodes_to_remove = sorted(random.sample(range(1, len(path.nodes) - 1), 2))
            if abs(nodes_to_remove[1] - nodes_to_remove[0]) > 1:
                break

        # Remove the nodes in descending order to avoid index shifting
        for index in sorted(nodes_to_remove, reverse=True):
            unassigned.append(path.nodes.pop(index))

        # Recalculate the path cost using the graph
        path.path_cost = state.graph_api.calculate_path_cost(path.nodes)

    # Create the new CevrpState
    return CevrpState(paths_copy, unassigned, state.graph_api)
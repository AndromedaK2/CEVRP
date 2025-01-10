import random
from ALNS_METAHEURISTIC.solution_state import CevrpState
from Shared.path import Path


def random_destroy(paths: list[Path]) -> CevrpState:
    """
    Randomly destroys two pairs of segments from the given paths.

    :param paths: List of Path objects representing the current routes.
    :return: A new CevrpState object with updated paths and unassigned nodes.
    """
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
            raise ValueError("Each path must have at least four nodes to destroy two segments.")

        # Randomly select two indices for the segments
        segment_indices = sorted(random.sample(range(1, len(path.nodes) - 1), 2))

        # Remove the segments and add to unassigned nodes
        for index in reversed(segment_indices):  # Reverse to avoid index shifting
            unassigned.append(path.nodes.pop(index))

    # Create the new CevrpState
    return CevrpState(paths_copy, unassigned)

from typing import Optional

import numpy as np

from ALNS_METAHEURISTIC.repair_operators import adjacent_swap, general_swap, block_insertion, reverse_location
from ALNS_METAHEURISTIC.solution_state import CevrpState
from Shared.graph_api import GraphApi
from Shared.path import Path


def apply_2opt(path: Path, graph_api: GraphApi) -> Path:
    """
    Applies the 2-opt algorithm to optimize the given route.

    Args:
        path (Path): The initial path to optimize.
        graph_api (GraphApi): An API to calculate the cost of a path.

    Returns:
        Path: The optimized path.
    """
    # Handle edge case: 2-opt cannot be applied to paths with fewer than 3 nodes
    if len(path.nodes) < 3:
        return path

    best_route = path.copy()
    best_cost = best_route.path_cost
    n = len(path.nodes)

    # Iterate over all possible pairs of indices (i, j)
    for i in range(1, n - 1):
        for j in range(i + 1, n - 1):
            # Split the path into three segments
            x = path.nodes[:i]  # Nodes before index i
            y = path.nodes[i:j + 1]  # Nodes from i to j (inclusive)
            reversed_y = list(reversed(y))  # Reverse segment between i and j
            z = path.nodes[j + 1:]  # Nodes after index j

            # Construct new route by combining segments
            new_route = x + reversed_y + z

            new_cost = graph_api.calculate_path_cost(new_route)
            if new_cost < best_cost:
                best_route.nodes = new_route
                best_cost = new_cost
                best_route.path_cost = best_cost
    return best_route


def apply_3opt(path: Path, graph_api: GraphApi) -> Path:
    """
    Applies the 3-opt algorithm to optimize the given route.
    This heuristic removes three edges and reconnects the segments in the best possible way,
    focusing on minimizing the path cost.

    :param path: The current route to optimize.
    :param graph_api: Graph API instance for cost calculations.
    :return: The optimized Path instance.
    """
    best_route = path.copy()
    best_cost = path.path_cost

    for i in range(1, len(path.nodes) - 5):
        for j in range(i + 2, len(path.nodes) - 3):
            for k in range(j + 2, len(path.nodes) - 1):
                new_routes = [
                    path.nodes[:i] + path.nodes[i:j][::-1] + path.nodes[j:k][::-1] + path.nodes[k:],
                    path.nodes[:i] + path.nodes[j:k] + path.nodes[i:j] + path.nodes[k:],
                    path.nodes[:i] + path.nodes[j:k][::-1] + path.nodes[i:j] + path.nodes[k:],
                ]

                for new_route in new_routes:
                    new_cost = graph_api.calculate_path_cost(new_route)
                    if new_cost < best_cost:
                        best_route.nodes = new_route
                        best_cost = new_cost

    best_route.path_cost = best_cost
    return best_route

def apply_local_search(state: CevrpState, rng: Optional[np.random.RandomState] = None) -> CevrpState:
    """
    Applies a local search operator to improve the given CEVRP solution.
    A random local search operator is selected and applied.

    :param state: The current CEVRP state.
    :param rng: A numpy random number generator for reproducibility.
    :return: The improved CEVRP state.
    """
    # Define available local search operators
    local_search_operators = [adjacent_swap, general_swap, block_insertion, reverse_location]

    # Select a random operator using numpy random generator
    operator = rng.choice(local_search_operators)

    # Apply the selected operator and return the modified state
    return operator(state)
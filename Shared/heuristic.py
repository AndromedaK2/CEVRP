from typing import Optional

import numpy as np

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


def apply_local_search(state: CevrpState, rng: Optional[np.random.RandomState] = None):
    """
    Applies a local search operator to improve the given CEVRP solution.
    A random local search operator is selected and applied.

    :param state: The current CEVRP state.
    :param rng: A numpy random number generator for reproducibility.
    :return: The improved CEVRP state.
    """
    # Define available local search operators
    local_search_operators = [adjacent_swap_local_search,
                              block_insertion_local_search,
                              general_swap_local_search,
                              search_reverse_location_local_search,
                              single_insertion_local_search]

    # Select a random operator using numpy random generator
    operator = rng.choice(local_search_operators)

    # Apply the selected operator and return the modified state
    operator(state)
    state.graph_api.visualize_graph(state.paths, state.cevrp.charging_stations, state.cevrp.name)



def adjacent_swap_local_search(state: CevrpState, rng: Optional[np.random.RandomState] = None) -> None:
    """
    Applies an adjacent swap heuristic to improve routes in CEVRP, ensuring depots remain fixed.
    This function modifies the given state in-place instead of returning a new state.

    :param state: The current CEVRP state (modified in-place).
    :param rng: A numpy random number generator for reproducibility.
    """
    for path in state.paths:
        original_nodes = path.nodes
        best_cost = path.path_cost
        best_energy = path.energy

        # Iterate over customer nodes only (exclude depots at index 0 and -1)
        for i in range(1, len(original_nodes) - 2):
            # Swap adjacent nodes
            original_nodes[i], original_nodes[i + 1] = original_nodes[i + 1], original_nodes[i]

            # Calculate cost and energy
            new_cost = state.graph_api.calculate_path_cost(original_nodes)
            new_energy = state.calculate_path_energy(original_nodes, state.cevrp.charging_stations)

            # Check if swap improves cost and respects energy
            if new_cost < best_cost and new_energy <= state.cevrp.energy_capacity:
                best_cost = new_cost
                best_energy = new_energy
            else:
                # Revert swap if no improvement
                original_nodes[i], original_nodes[i + 1] = original_nodes[i + 1], original_nodes[i]

        # Update path properties after all swaps
        path.path_cost = best_cost
        path.energy = best_energy
        path.feasible = True  # Assumes swaps maintain feasibility


def general_swap_local_search(state: CevrpState, rng: Optional[np.random.RandomState] = None) -> None:
    """
    Applies a general swap heuristic to improve routes in CEVRP as a local search operator.
    Swaps non-consecutive nodes in each route and keeps the best feasible improvement.

    :param state: The current CEVRP state (modified in-place).
    :param rng: A numpy random number generator for reproducibility.
    """
    for path in state.paths:
        best_cost = state.graph_api.calculate_path_cost(path.nodes)
        best_energy = state.get_path_energy_consumption(path.nodes)

        for i in range(1, len(path.nodes) - 3):  # Exclude depot
            for j in range(i + 2, len(path.nodes) - 1):
                # Swap non-consecutive nodes
                path.nodes[i], path.nodes[j] = path.nodes[j], path.nodes[i]

                # Calculate new cost and energy
                new_cost = state.graph_api.calculate_path_cost(path.nodes)
                new_energy = state.calculate_path_energy(path.nodes, state.cevrp.charging_stations)

                # Keep the change if it improves cost and maintains energy feasibility
                if new_cost < best_cost and new_energy <= state.cevrp.energy_capacity:
                    best_cost = new_cost
                    best_energy = new_energy
                else:
                    # Revert swap if no improvement
                    path.nodes[i], path.nodes[j] = path.nodes[j], path.nodes[i]

        # Update path properties after all swaps
        path.path_cost = best_cost
        path.energy = best_energy


def single_insertion_local_search(state: CevrpState, rng: Optional[np.random.RandomState] = None) -> None:
    """
    Applies a single insertion heuristic to improve routes in CEVRP.
    Removes a node and reinserts it in another position, ensuring feasibility.

    :param state: The current CEVRP state (modified in-place).
    :param rng: A numpy random number generator for reproducibility.
    """
    for path in state.paths:
        best_cost = state.graph_api.calculate_path_cost(path.nodes)
        best_energy = state.get_path_energy_consumption(path.nodes)

        for i in range(1, len(path.nodes) - 1):  # Exclude depot
            for j in range(1, len(path.nodes) - 1):
                if i != j:
                    # Move node i to position j
                    path.nodes.insert(j, path.nodes.pop(i))

                    # Calculate new cost and energy
                    new_cost = state.graph_api.calculate_path_cost(path.nodes)
                    new_energy = state.calculate_path_energy(path.nodes, state.cevrp.charging_stations)

                    # Keep change if it improves cost and maintains feasibility
                    if new_cost < best_cost and new_energy <= state.cevrp.energy_capacity:
                        best_cost = new_cost
                        best_energy = new_energy
                    else:
                        # Revert insertion if no improvement
                        path.nodes.insert(i, path.nodes.pop(j))

        # Update path properties after all insertions
        path.path_cost = best_cost
        path.energy = best_energy


def block_insertion_local_search(state: CevrpState, rng: Optional[np.random.RandomState] = None) -> None:
    """
    Applies a block insertion heuristic to improve routes in CEVRP.
    Moves a block of consecutive nodes to a different position, ensuring feasibility.

    :param state: The current CEVRP state (modified in-place).
    :param rng: A numpy random number generator for reproducibility.
    """
    for path in state.paths:
        best_cost = state.graph_api.calculate_path_cost(path.nodes)
        best_energy = state.get_path_energy_consumption(path.nodes)

        for b in range(2, len(path.nodes) - 3):  # Block size
            for i in range(1, len(path.nodes) - 1 - b):  # Start index
                for j in range(i + b, len(path.nodes) - 1):  # Insertion index
                    # Move block i:i+b to position j
                    block = path.nodes[i:i + b]
                    path.nodes = path.nodes[:i] + path.nodes[i + b:j + 1] + block + path.nodes[j + 1:]

                    # Calculate new cost and energy
                    new_cost = state.graph_api.calculate_path_cost(path.nodes)
                    new_energy = state.calculate_path_energy(path.nodes, state.cevrp.charging_stations)

                    # Keep change if it improves cost and maintains feasibility
                    if new_cost < best_cost and new_energy <= state.cevrp.energy_capacity:
                        best_cost = new_cost
                        best_energy = new_energy
                    else:
                        # Revert block movement if no improvement
                        path.nodes = path.nodes[:i] + block + path.nodes[i:j + 1] + path.nodes[j + 1:]

        # Update path properties after all block insertions
        path.path_cost = best_cost
        path.energy = best_energy


def search_reverse_location_local_search(state: CevrpState, rng: Optional[np.random.RandomState] = None) -> None:
    """
    Applies a reverse location heuristic to improve routes in CEVRP.
    Reverses a segment of the route while ensuring feasibility.

    :param state: The current CEVRP state (modified in-place).
    :param rng: A numpy random number generator for reproducibility.
    """
    for path in state.paths:
        best_cost = state.graph_api.calculate_path_cost(path.nodes)
        best_energy = state.get_path_energy_consumption(path.nodes)

        for i in range(1, len(path.nodes) - 3):  # Start index
            for j in range(i + 2, len(path.nodes) - 1):  # End index
                # Reverse segment between i and j
                path.nodes[i:j+1] = reversed(path.nodes[i:j+1])

                # Calculate new cost and energy
                new_cost = state.graph_api.calculate_path_cost(path.nodes)
                new_energy = state.calculate_path_energy(path.nodes, state.cevrp.charging_stations)

                # Keep change if it improves cost and maintains feasibility
                if new_cost < best_cost and new_energy <= state.cevrp.energy_capacity:
                    best_cost = new_cost
                    best_energy = new_energy
                else:
                    # Revert reversal if no improvement
                    path.nodes[i:j+1] = reversed(path.nodes[i:j+1])

        # Update path properties after all reversals
        path.path_cost = best_cost
        path.energy = best_energy

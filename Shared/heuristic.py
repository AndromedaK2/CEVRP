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
    #state.graph_api.visualize_graph(state.paths, state.cevrp.charging_stations, state.cevrp.name)


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
    Moves a block of consecutive nodes to a different position while ensuring feasibility.

    :param state: The current CEVRP state (modified in-place).
    :param rng: Optional numpy random state for reproducibility.
    """
    if rng is None:
        rng = np.random.default_rng()  # Create a new RNG if none is provided

    for path in state.paths:
        if len(path.nodes) < 5:  # Skip paths too short for meaningful block moves
            continue

        current_cost = state.graph_api.calculate_path_cost(path.nodes)

        # Determine feasible block size (2 <= size < len(path.nodes) - 1)
        max_block_size = min(4, len(path.nodes) - 2)  # Ensure block can be extracted without including depots
        if max_block_size < 2:
            continue
        block_size = rng.integers(2, max_block_size + 1)

        # Select block start index (avoiding depot at 0)
        start_idx = rng.integers(1, len(path.nodes) - block_size)

        # Extract block and create remaining nodes
        block = path.nodes[start_idx:start_idx + block_size]
        remaining_nodes = path.nodes[:start_idx] + path.nodes[start_idx + block_size:]

        # Choose insertion point in remaining nodes (all valid positions)
        insert_idx = rng.integers(0, len(remaining_nodes) + 1)  # +1 to allow insertion at end

        # Reconstruct path with block inserted
        new_nodes = remaining_nodes[:insert_idx] + block + remaining_nodes[insert_idx:]

        # Validate new path's feasibility and improvement
        new_cost = state.graph_api.calculate_path_cost(new_nodes)
        new_energy = state.calculate_path_energy(new_nodes, state.cevrp.charging_stations)

        if new_cost < current_cost and new_energy <= state.cevrp.energy_capacity:
            path.nodes[:] = new_nodes
            path.path_cost = new_cost
            path.energy = new_energy


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

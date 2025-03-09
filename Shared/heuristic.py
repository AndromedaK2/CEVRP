from typing import Optional, List

import numpy as np

from ALNS_METAHEURISTIC.solution_state import CevrpState
from Shared.cevrp import CEVRP
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


def apply_2opt_star(paths: List[Path], graph_api: GraphApi, cevrp: CEVRP) -> List[Path]:
    """
    Applies the 2-opt* algorithm to optimize inter route connections in a list of paths.
    Swaps the tails or heads of different routes to reduce cost while ensuring feasibility.

    Args:
        paths (List[Path]): The list of routes to optimize.
        graph_api (GraphApi): API to calculate path costs.
        cevrp (CEVRP): An instance of CEVRP.

    Returns:
        List[Path]: The optimized list of paths after 2-opt*.

    """

    best_paths = [path.copy() for path in paths]
    improved = False  # Track whether an improvement has been made

    # Iterate over all route pairs
    for idx1 in range(len(best_paths)):
        for idx2 in range(idx1 + 1, len(best_paths)):  # Avoid self-swaps
            route1, route2 = best_paths[idx1], best_paths[idx2]

            if len(route1.nodes) < 3 or len(route2.nodes) < 3:
                continue  # Skip routes that are too short for swapping

            # Try swapping tails of both routes
            for i in range(1, len(route1.nodes) - 1):  # Avoid depot
                for j in range(1, len(route2.nodes) - 1):  # Avoid depot
                    new_route1_nodes = route1.nodes[:i] + route2.nodes[j:]
                    new_route2_nodes = route2.nodes[:j] + route1.nodes[i:]

                    # Ensure depot remains at the start and end
                    new_route1_nodes = fix_depot(new_route1_nodes, route1.nodes[0])
                    new_route2_nodes = fix_depot(new_route2_nodes, route2.nodes[0])

                    # Check feasibility
                    if not graph_api.is_feasible(new_route1_nodes, new_route2_nodes,cevrp.capacity):
                        continue  # Skip this swap if infeasible

                    # Calculate new cost
                    new_cost1 = graph_api.calculate_path_cost(new_route1_nodes)
                    new_cost2 = graph_api.calculate_path_cost(new_route2_nodes)
                    old_cost = route1.path_cost + route2.path_cost
                    new_total_cost = new_cost1 + new_cost2

                    # If the new configuration is better, update routes
                    if new_total_cost < old_cost:
                        route1.nodes, route2.nodes = new_route1_nodes, new_route2_nodes
                        route1.path_cost, route2.path_cost = new_cost1, new_cost2
                        improved = True

            if improved:
                break  # Stop further swaps if an improvement was made

    return best_paths


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

    # Apply the selected operator
    operator(state)

    # Get operator name for the title
    operator_name = operator.__name__

    # Visualize with operator name in the title
    title = f"Local Search: {operator_name} - {state.cevrp.name}"
    state.graph_api.visualize_graph(state.paths, state.cevrp.charging_stations, title)


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

        # Ensure depot remains at the beginning and end
        depot = path.nodes[0]
        if path.nodes[-1] != depot:
            continue  # Ensure paths are well-formed

        # Determine feasible block size (2 ≤ size < len(path.nodes) - 1)
        max_block_size = min(4, len(path.nodes) - 2)  # Ensure block can be extracted without including depots
        if max_block_size < 2:
            continue
        block_size = rng.integers(2, max_block_size + 1)

        # Select block start index (avoiding depot at 0 and end)
        start_idx = rng.integers(1, len(path.nodes) - block_size - 1)

        # Extract block and create remaining nodes
        block = path.nodes[start_idx:start_idx + block_size]
        remaining_nodes = path.nodes[:start_idx] + path.nodes[start_idx + block_size:]

        # Ensure the depot is preserved at the start and end
        if remaining_nodes[0] != depot or remaining_nodes[-1] != depot:
            continue

        # Choose insertion point in remaining nodes (avoiding depot at start)
        insert_idx = rng.integers(1, len(remaining_nodes))  # Must be within valid positions

        # Reconstruct path with block inserted
        new_nodes = remaining_nodes[:insert_idx] + block + remaining_nodes[insert_idx:]

        # Validate new path's feasibility
        new_cost = state.graph_api.calculate_path_cost(new_nodes)
        new_energy = state.calculate_path_energy(new_nodes, state.cevrp.charging_stations)

        # Ensure connectivity is preserved
        if (
                new_cost < current_cost and
                new_energy <= state.cevrp.energy_capacity and
                state.graph_api.is_path_connected(new_nodes)
        ):
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
                path.nodes[i:j + 1] = reversed(path.nodes[i:j + 1])

                # Calculate new cost and energy
                new_cost = state.graph_api.calculate_path_cost(path.nodes)
                new_energy = state.calculate_path_energy(path.nodes, state.cevrp.charging_stations)

                # Keep change if it improves cost and maintains feasibility
                if new_cost < best_cost and new_energy <= state.cevrp.energy_capacity:
                    best_cost = new_cost
                    best_energy = new_energy
                else:
                    # Revert reversal if no improvement
                    path.nodes[i:j + 1] = reversed(path.nodes[i:j + 1])

        # Update path properties after all reversals
        path.path_cost = best_cost
        path.energy = best_energy


def fix_depot(nodes: List[str], depot: str) -> List[str]:
    """
    Ensures the depot remains at the start and end of the route.

    Args:
        nodes (List[str]): The modified list of nodes.
        depot (str): The depot node.

    Returns:
        List[str]: The corrected route with depot in place.
    """
    if nodes[0] != depot:
        nodes.insert(0, depot)
    if nodes[-1] != depot:
        nodes.append(depot)
    return nodes

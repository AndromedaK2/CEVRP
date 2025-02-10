import random
from typing import Optional
from ALNS_METAHEURISTIC.solution_state import CevrpState
from Shared.config import DEFAULT_SOURCE_NODE
from Shared.path import Path


def random_destroy(state: CevrpState, rnd_state: Optional[random.Random] = None) -> CevrpState:
    """
    Randomly removes nodes from paths while ensuring energy capacity constraints.

    :param state: Current solution state (CevrpState).
    :param rnd_state: Random number generator state (optional).
    :return: A new CevrpState object with updated paths and unassigned nodes.
    :raises ValueError: If there are fewer than two paths or paths with insufficient nodes.
    """

    paths = state.paths
    energy_capacity = state.cevrp.energy_capacity

    if len(paths) < 2:
        raise ValueError("At least two paths are required to perform destruction.")

    paths_copy = [path.copy() for path in paths]
    path_indices = random.sample(range(len(paths_copy)), 2)
    selected_paths = [paths_copy[i] for i in path_indices]
    unassigned = state.unassigned.copy()

    for path in selected_paths:
        if len(path.nodes) < 2:
            continue

        energy_consumption = 0
        valid_path = Path()

        for i in range(len(path.nodes) - 1):
            current_node, next_node = path.nodes[i], path.nodes[i + 1]
            energy_consumption += state.get_edge_energy_consumption(current_node, next_node)

            if energy_consumption > energy_capacity:
                valid_path.nodes.append(DEFAULT_SOURCE_NODE)
                break

            valid_path.nodes.append(current_node)

        if energy_consumption > energy_capacity:
            nodes_to_remove = set(path.nodes) - set(valid_path.nodes)
        else:
            if len(path.nodes) > 4:
                nodes_to_remove = set(random.sample(path.nodes[1:-1], 2))
            elif len(path.nodes) > 2:
                nodes_to_remove = {random.choice(path.nodes[1:-1])}
            else:
                nodes_to_remove = set()

        path.nodes[:] = [node for node in path.nodes if node not in nodes_to_remove]
        unassigned.extend(nodes_to_remove)

        path.path_cost = state.graph_api.calculate_path_cost(path.nodes)
        path.demand = state.graph_api.get_total_demand_path(path.nodes)

    return CevrpState(paths_copy, unassigned, state.graph_api, state.cevrp)



def remove_overcapacity_nodes(state: CevrpState, rnd_state: Optional[random.Random] = None) -> CevrpState:
    """
    Removes nodes from paths exceeding the maximum energy capacity while ensuring a safe return to the depot.

    :param state: Current solution state (CevrpState).
    :param rnd_state: Random number generator state (optional).
    :return: A new CevrpState object with updated paths and unassigned nodes.
    """

    paths = state.paths
    energy_capacity = state.cevrp.energy_capacity

    if len(paths) < 2:
        raise ValueError("At least two paths are required to perform this operation.")

    paths_copy = [path.copy() for path in paths]
    unassigned = state.unassigned.copy()

    for path in paths_copy:
        if len(path.nodes) < 4:
            continue

        energy_consumption = 0
        valid_path = Path()

        for i in range(len(path.nodes) - 1):
            current_node, next_node = path.nodes[i], path.nodes[i + 1]

            # Compute the additional energy required before adding it
            additional_energy = state.get_edge_energy_consumption(current_node, next_node)

            # Check if the vehicle can safely reach the next node
            if energy_consumption + additional_energy > energy_capacity:
                # Before stopping, check if it has enough energy to return to depot
                depot_return_energy = state.get_edge_energy_consumption(current_node, DEFAULT_SOURCE_NODE)

                if energy_consumption + depot_return_energy <= energy_capacity:
                    valid_path.nodes.append(DEFAULT_SOURCE_NODE)  # Safe return
                break  # Stop before exceeding capacity

            # Only add the node if it doesn't exceed capacity
            valid_path.nodes.append(current_node)
            energy_consumption += additional_energy  # Update consumption after confirming feasibility

        # Ensure the vehicle can return to depot from the last valid node
        if valid_path.nodes and valid_path.nodes[-1] != DEFAULT_SOURCE_NODE:
            last_node = valid_path.nodes[-1]
            depot_return_energy = state.get_edge_energy_consumption(last_node, DEFAULT_SOURCE_NODE)

            if energy_consumption + depot_return_energy <= energy_capacity:
                valid_path.nodes.append(DEFAULT_SOURCE_NODE)  # Add depot only if feasible

        # Nodes to remove are those that were not included in valid_path
        nodes_to_remove = set(path.nodes) - set(valid_path.nodes)

        path.nodes[:] = [node for node in path.nodes if node not in nodes_to_remove]
        unassigned.extend(nodes_to_remove)

        path.path_cost = state.graph_api.calculate_path_cost(path.nodes)
        path.demand = state.graph_api.get_total_demand_path(path.nodes)
        path.energy = energy_consumption

    return CevrpState(paths_copy, unassigned, state.graph_api, state.cevrp)

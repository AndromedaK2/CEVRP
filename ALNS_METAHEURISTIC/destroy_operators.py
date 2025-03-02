from typing import Optional

import numpy as np

from ALNS_METAHEURISTIC.solution_state import CevrpState
from Shared.config import DEFAULT_SOURCE_NODE
from Shared.path import Path


def remove_overcapacity_nodes(state: CevrpState, rnd_state: Optional[np.random.RandomState] = None) -> CevrpState:
    """
    Removes nodes from paths exceeding the maximum energy capacity while ensuring a safe return to the depot.
    Charging stations reset energy consumption and recharge the battery.
    Also removes routes with only two nodes (one customer + depot).
    Prevents getting stuck by applying randomized removal of excess nodes.

    :param state: Current solution state (CevrpState).
    :param rnd_state: Random number generator state (optional).
    :return: A new CevrpState object with updated paths and unassigned nodes.
    """
    state_copy = state.copy()
    paths = state_copy.paths
    energy_capacity = state_copy.cevrp.energy_capacity
    charging_stations = set(state_copy.cevrp.charging_stations)

    if len(paths) < 2:
        raise ValueError("At least two paths are required to perform this operation.")

    unassigned = set(state_copy.unassigned)
    new_paths = []  # Store valid paths
    energy_cache = {}

    for path in paths:
        nodes = path.nodes
        num_nodes = len(nodes)
        # **Remove paths that contain only the depot and one customer**
        if num_nodes <= 3:
            unassigned.update(node for node in nodes if node != DEFAULT_SOURCE_NODE)
            continue

        energy_consumption = 0
        valid_nodes = [nodes[0]]

        for i in range(num_nodes - 1):
            current_node, next_node = nodes[i], nodes[i + 1]

            # **Reset energy at charging stations**
            if current_node in charging_stations:
                energy_consumption = 0  # Fully recharge

            # Compute additional energy needed to reach the next node
            edge = (current_node, next_node)
            if edge not in energy_cache:
                energy_cache[edge] = state_copy.get_edge_energy_consumption(current_node, next_node)
            additional_energy = energy_cache[edge]


            # **Check if the vehicle can safely reach the next node**
            if energy_consumption + additional_energy > energy_capacity:
                valid_nodes.pop(-1)
                break  # Stop before exceeding capacity

            # Add the node only if it doesn't exceed capacity
            valid_nodes.append(next_node)
            energy_consumption += additional_energy

        # Nodes that couldn't be added
        remaining_nodes = nodes[len(valid_nodes):]
        # **Filter out charging stations from unassigned nodes**
        unassigned.update(node for node in remaining_nodes if node != DEFAULT_SOURCE_NODE and node not in charging_stations)

        # **Recalculate cost, demand, and energy**
        if len(valid_nodes) > 1:
            valid_path = Path()
            valid_path.nodes = valid_nodes
            valid_path.path_cost = state_copy.graph_api.calculate_path_cost(valid_nodes)
            valid_path.demand = state_copy.graph_api.get_total_demand_path(valid_nodes)
            valid_path.energy = energy_consumption
            valid_path.feasible = (
                valid_nodes[0] == DEFAULT_SOURCE_NODE
                and valid_nodes[-1] == DEFAULT_SOURCE_NODE
                and len(valid_nodes) > 2
            )
            new_paths.append(valid_path)

    # **Filter out charging stations from the final unassigned list**
    unassigned = list(unassigned - charging_stations)
    state_copy.graph_api.visualize_graph(new_paths, charging_stations, state_copy.cevrp.name)
    return CevrpState(new_paths, unassigned, state_copy.graph_api, state_copy.cevrp)


def remove_charging_station(state: CevrpState, rnd_state: Optional[np.random.RandomState] = None) -> CevrpState:
    """
    Randomly removes one instance of a duplicated charging station from a route
    while keeping the energy constraint valid.

    :param state: The current CevrpState containing the solution.
    :param rnd_state: Random number generator state.
    :return: A new CevrpState with modified routes.
    """
    state_copy = state.copy()
    modified_paths = []

    for path in state_copy.paths:
        station_positions = [i for i, node in enumerate(path.nodes) if node in state_copy.cevrp.charging_stations]

        if len(station_positions) < 2:
            # If there are no duplicates, keep the path unchanged
            modified_paths.append(path)
            continue

        # Select a random charging station instance to remove
        index_to_remove = rnd_state.choice(station_positions) if rnd_state else np.random.choice(station_positions)
        modified_nodes = path.nodes[:index_to_remove] + path.nodes[index_to_remove + 1:]

        # Recalculate energy consumption
        energy_used = 0
        for i in range(len(modified_nodes) - 1):
            current_node, next_node = modified_nodes[i], modified_nodes[i + 1]

            # Reset energy if the current node is a charging station
            if current_node in state_copy.cevrp.charging_stations:
                energy_used = 0

            energy_used += state_copy.get_edge_energy_consumption(current_node, next_node)

            # If energy constraint is violated, revert the change
            if energy_used > state_copy.cevrp.energy_capacity:
                modified_paths.append(path)  # Keep original path
                break
        else:
            # If the removal is feasible, update the path
            new_path = Path()
            new_path.nodes = modified_nodes
            new_path.path_cost = state_copy.graph_api.calculate_path_cost(modified_nodes)
            new_path.energy = energy_used
            new_path.demand = state_copy.graph_api.get_total_demand_path(modified_nodes)
            new_path.feasible = True
            modified_paths.append(new_path)

    state_copy.graph_api.visualize_graph(modified_paths, state_copy.cevrp.charging_stations, state_copy.cevrp.name)
    return CevrpState(modified_paths, state_copy.unassigned, state_copy.graph_api, state_copy.cevrp)


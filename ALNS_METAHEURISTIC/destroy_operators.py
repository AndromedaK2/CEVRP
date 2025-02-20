import copy
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
    charging_stations = state_copy.cevrp.charging_stations

    if len(paths) < 2:
        raise ValueError("At least two paths are required to perform this operation.")

    paths_copy = [path.copy() for path in paths]
    unassigned = state_copy.unassigned
    new_paths = []  # Store valid paths

    for path in paths_copy:
        # **Remove paths that contain only the depot and one customer**
        if len(path.nodes) <= 3:
            unassigned.extend([node for node in path.nodes if node != DEFAULT_SOURCE_NODE])
            continue  # Skip this path (remove it)

        energy_consumption = 0
        valid_path = Path()
        valid_path.nodes.append(path.nodes[0])

        for i in range(len(path.nodes) - 1):
            current_node, next_node = path.nodes[i], path.nodes[i + 1]

            # **Reset energy at charging stations**
            if current_node in charging_stations:
                energy_consumption = 0  # Fully recharge

            # Compute additional energy needed to reach the next node
            additional_energy = state_copy.get_edge_energy_consumption(current_node, next_node)

            # **Check if the vehicle can safely reach the next node**
            if energy_consumption + additional_energy > energy_capacity:
                break  # Stop before exceeding capacity

            # Add the node only if it doesn't exceed capacity
            valid_path.nodes.append(next_node)
            energy_consumption += additional_energy

        # **Handle unassigned nodes properly**
        remaining_nodes = path.nodes[len(valid_path.nodes):]  # Nodes that couldn't be added

        if remaining_nodes:
            # **Filter out charging stations from unassigned nodes**
            unassigned.extend([node for node in remaining_nodes if node != DEFAULT_SOURCE_NODE and node not in charging_stations])

        # **Recalculate cost, demand, and energy**
        if valid_path.nodes:
            valid_path.path_cost = state_copy.graph_api.calculate_path_cost(valid_path.nodes)
            valid_path.demand = state_copy.graph_api.get_total_demand_path(valid_path.nodes)
            valid_path.energy = energy_consumption

        # **Only keep the path if it starts and ends at the depot**
        if len(valid_path.nodes) > 2 and valid_path.nodes[0] == DEFAULT_SOURCE_NODE and valid_path.nodes[-1] == DEFAULT_SOURCE_NODE:
            valid_path.feasible = True
            new_paths.append(valid_path)
        else:
            new_paths.append(valid_path)
            valid_path.feasible = False
    # **Filter out charging stations from the final unassigned list**
    unassigned = [node for node in unassigned if node not in charging_stations]
    rnd_state.shuffle(unassigned)
    rnd_state.shuffle(new_paths)
    return CevrpState(new_paths, unassigned, state_copy.graph_api, state_copy.cevrp)



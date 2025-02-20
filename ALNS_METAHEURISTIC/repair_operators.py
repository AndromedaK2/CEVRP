import copy

import numpy as np
from typing import Optional

from ALNS_METAHEURISTIC.solution_state import CevrpState
from Shared.config import DEFAULT_SOURCE_NODE
from Shared.path import Path


def find_best_charging_station(state, last_node, energy_capacity, energy_consumption, charging_stations, current_energy):
    """Finds the best charging station within energy constraints."""
    best_station, best_station_cost = None, float('inf')
    for station in charging_stations:
        if station != last_node:
            energy_required = state.graph_api.calculate_edge_energy_consumption(last_node, station, energy_consumption)
            if current_energy + energy_required < energy_capacity:
                cost = state.graph_api.get_edge_cost(last_node, station)
                if cost < best_station_cost:
                    best_station, best_station_cost = station, cost
    return best_station


def calculate_path_energy(state, nodes, charging_stations):
    """Calculates total energy usage for a path with resets at charging stations."""
    energy = 0
    for i in range(1, len(nodes)):
        if nodes[i - 1] in charging_stations:
            energy = 0
        energy += state.get_edge_energy_consumption(nodes[i - 1], nodes[i])
    return energy


def find_highest_energy_pair(state, nodes):
    """
    Finds the consecutive node pair with the highest energy consumption in a given route.

    :param state: CevrpState instance containing energy calculations.
    :param nodes: List of nodes in the current route.
    :return: Tuple (index, node1, node2, max_energy) where:
             - index is the position where the charging station should be inserted.
             - node1 and node2 are the nodes in the highest energy-consuming edge.
             - max_energy is the energy required for that edge.
    """
    max_energy = -float('inf')
    best_index = None
    best_pair = None

    for i in range(len(nodes) - 1):
        node1, node2 = nodes[i], nodes[i + 1]
        energy_consumption = state.get_edge_energy_consumption(node1, node2)

        if energy_consumption > max_energy:
            max_energy = energy_consumption
            best_index = i  # Insert the station after node1
            best_pair = (node1, node2)

    return best_index, best_pair[0], best_pair[1], max_energy



def insert_charging_station_at_highest_energy(state, path):
    """
    Inserts a charging station at the highest energy-consuming edge in a route.

    :param state: CevrpState instance containing graph details.
    :param path: Path object representing the route.
    :return: Updated path with a charging station inserted.
    """
    charging_stations = state.cevrp.charging_stations
    best_index, node1, node2, max_energy = find_highest_energy_pair(state, path.nodes)

    if best_index is None:
        return path  # No changes if there's no valid high-energy edge.

    # Find the best charging station to insert
    station = find_best_charging_station(state, node1, state.cevrp.energy_capacity, state.cevrp.energy_consumption, charging_stations, max_energy)

    if station:
        path.nodes.insert(best_index + 1, station)  # Insert after node1
        path.energy = calculate_path_energy(state, path.nodes, charging_stations)  # Recalculate energy usage

    return path



def smart_reinsertion(state: CevrpState, rnd_state: Optional[np.random.RandomState] = None) -> CevrpState:
    """Reinserts unassigned nodes into feasible routes, ensuring constraints."""
    state_copy = state.copy()
    paths_copy = state_copy.paths
    feasible_paths = [path.copy() for path in paths_copy if path.feasible]
    not_feasible_paths = [path.copy() for path in paths_copy if not path.feasible]
    unassigned_copy    =  copy.deepcopy(state_copy.unassigned)
    charging_stations  = state_copy.cevrp.charging_stations

    visited_nodes = {node for path in paths_copy for node in path.nodes if node != DEFAULT_SOURCE_NODE}
    unassigned_copy = [node for node in unassigned_copy if node not in visited_nodes]

    rnd_state.shuffle(unassigned_copy)

    for modified_path in not_feasible_paths:
        i = 0
        while i < len(unassigned_copy):
            node = unassigned_copy[i]
            if node in visited_nodes:
                i += 1
                continue

            candidate_path = modified_path.copy()
            insert_position = len(candidate_path.nodes) - 1 if candidate_path.nodes[-1] == DEFAULT_SOURCE_NODE else len(candidate_path.nodes)
            energy_used = candidate_path.energy
            prev_node = modified_path.nodes[insert_position - 1]

            if prev_node not in charging_stations:
                energy_to_node = state_copy.get_edge_energy_consumption(prev_node, node)
                if energy_used + energy_to_node > state_copy.cevrp.energy_capacity:
                    station_to_add = find_best_charging_station(
                        state_copy, prev_node, state_copy.cevrp.energy_capacity,
                        state_copy.cevrp.energy_consumption, charging_stations, energy_used)
                    if station_to_add:
                        candidate_path.nodes.insert(insert_position, station_to_add)
                        insert_position += 1
                        candidate_path.nodes.insert(insert_position, node)
                        candidate_path.energy = state_copy.get_edge_energy_consumption(station_to_add, node)
                    else:
                        i += 1
                        continue
                else:
                    candidate_path.nodes.insert(insert_position, node)
                    candidate_path.energy += energy_to_node

            elif prev_node in charging_stations:
                # Construct candidate path with node insertion
                energy_to_node = state_copy.get_edge_energy_consumption(prev_node, node)
                candidate_path.nodes.insert(insert_position, node)
                candidate_path.energy = energy_to_node

            candidate_path.demand = state_copy.graph_api.get_total_demand_path(candidate_path.nodes)
            if candidate_path.demand <= state_copy.cevrp.capacity:
                modified_path.nodes = candidate_path.nodes.copy()
                modified_path.path_cost = state_copy.graph_api.calculate_path_cost(candidate_path.nodes)
                modified_path.energy = candidate_path.energy
                modified_path.demand = candidate_path.demand
                visited_nodes.add(node)
                unassigned_copy.pop(i)
            i += 1
        # Ensure all routes end at the depot
    paths_final:list[Path] = []

    for original_path in not_feasible_paths:
        modified_path = original_path.copy()
        modified_path.nodes = original_path.nodes.copy()

        if modified_path.nodes[-1] != DEFAULT_SOURCE_NODE:

            current_energy = modified_path.energy
            last_node = modified_path.nodes[-1]

            if last_node not in charging_stations:
                energy_to_depot = state_copy.get_edge_energy_consumption(last_node, DEFAULT_SOURCE_NODE)

                if current_energy + energy_to_depot > state_copy.cevrp.energy_capacity:
                    station = find_best_charging_station(
                        state_copy,
                        last_node=last_node,
                        energy_capacity=state_copy.cevrp.energy_capacity,
                        energy_consumption=state_copy.cevrp.energy_consumption,
                        charging_stations=charging_stations,
                        current_energy=current_energy
                    )

                    if station:
                        modified_path.nodes.append(station)
                        modified_path.energy = 0
                        energy_to_depot = state_copy.get_edge_energy_consumption(station, DEFAULT_SOURCE_NODE)
                        modified_path.nodes.append(DEFAULT_SOURCE_NODE)
                        modified_path.energy += energy_to_depot
                    else:
                        #modified_path = insert_charging_station_at_highest_energy(state_copy, modified_path)
                        #modified_path.energy = calculate_path_energy(state_copy, modified_path.nodes,charging_stations )
                        #modified_path.path_cost = state_copy.graph_api.calculate_path_cost(modified_path.nodes)
                        modified_path.feasible = False
                        paths_final.append(modified_path)
                        continue
                else:
                    modified_path.nodes.append(DEFAULT_SOURCE_NODE)
                    modified_path.energy += energy_to_depot
            else:
                energy_to_depot = state_copy.get_edge_energy_consumption(last_node, DEFAULT_SOURCE_NODE)
                modified_path.nodes.append(DEFAULT_SOURCE_NODE)
                modified_path.energy = energy_to_depot

        modified_path.path_cost = state_copy.graph_api.calculate_path_cost(modified_path.nodes)
        modified_path.feasible = True

        paths_final.append(modified_path)

    unassigned_final = [node for node in unassigned_copy if node not in visited_nodes]

    paths_final = paths_final + feasible_paths


    return CevrpState(
        paths=paths_final,
        unassigned=unassigned_final,
        graph_api=state.graph_api,
        cevrp=state.cevrp
    )
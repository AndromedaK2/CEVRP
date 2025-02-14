import copy
import numpy as np
from typing import Optional
from ALNS_METAHEURISTIC.solution_state import CevrpState
from Shared.config import DEFAULT_SOURCE_NODE


def find_best_charging_station(state, last_node, energy_capacity, energy_consumption, charging_stations, current_energy):
    """
    Finds the best charging station to insert before a new node if needed.
    Iterates through all charging stations to find the closest one within the remaining energy range.
    """
    best_station = None
    best_station_cost = float('inf')
    for station in charging_stations:
        if station == last_node:
            continue
        # Calculate energy required to reach the station
        energy_required = state.graph_api.calculate_edge_energy_consumption(last_node, station, energy_consumption)
        # Check feasibility
        if current_energy + energy_required <= energy_capacity:
            cost = state.graph_api.get_edge_cost(last_node, station)
            # Track the station with the lowest cost
            if cost < best_station_cost:
                best_station = station
                best_station_cost = cost
    return best_station


def calculate_path_energy(state, nodes, charging_stations):
    """
    Calculates the total energy usage for a given path, considering resets at charging stations.
    """
    energy = 0
    for i in range(1, len(nodes)):
        # Reset energy at charging stations
        if nodes[i - 1] in charging_stations:
            energy = 0
        energy += state.get_edge_energy_consumption(nodes[i - 1], nodes[i])
    return energy


def smart_reinsertion(state: CevrpState, rnd_state: Optional[np.random.RandomState] = None) -> CevrpState:
    """
    Reinserts unassigned nodes into feasible routes while ensuring:
    - No duplicate nodes in any route.
    - Charging stations are inserted only when necessary.
    - All routes remain energy-feasible and return to the depot.
    - Returns a new CevrpState object with the updated paths.
    """
    # Deep copy to avoid modifying the original state
    state_copy = copy.deepcopy(state)

    # Copy paths and unassigned nodes
    paths_copy = [path.copy() for path in state_copy.paths]
    unassigned_copy = state_copy.unassigned.copy()

    # Extract necessary parameters
    energy_capacity = state_copy.cevrp.energy_capacity
    energy_consumption = state_copy.cevrp.energy_consumption
    charging_stations = state_copy.cevrp.charging_stations

    # Track assigned nodes to avoid duplicates
    visited_nodes = {node for path in paths_copy for node in path.nodes if node != DEFAULT_SOURCE_NODE}
    unassigned_copy = [node for node in unassigned_copy if node not in visited_nodes]

    # Shuffle unassigned nodes for diversity
    if rnd_state:
        rnd_state.shuffle(unassigned_copy)
    else:
        np.random.shuffle(unassigned_copy)

    # Attempt to insert unassigned nodes into existing routes
    for path in paths_copy:
        i = 0
        while i < len(unassigned_copy):
            node = unassigned_copy[i]
            if node in visited_nodes:
                i += 1
                continue

            # Determine insertion position (before depot if present)
            insert_position = len(path.nodes) - 1 if path.nodes[-1] == DEFAULT_SOURCE_NODE else len(path.nodes)

            # Calculate current energy usage
            energy_used = calculate_path_energy(state_copy, path.nodes, charging_stations)

            # Check for necessary charging station insertion
            prev_node = path.nodes[insert_position - 1]
            station_to_add = None
            if prev_node not in charging_stations:
                station_to_add = find_best_charging_station(
                    state_copy, prev_node, energy_capacity, energy_consumption, charging_stations, energy_used
                )

            # Construct candidate path with node insertion
            candidate_path = path.copy()
            if station_to_add:
                candidate_path.nodes.insert(insert_position, station_to_add)
                insert_position += 1
            candidate_path.nodes.insert(insert_position, node)

            # Calculate energy usage for candidate path
            energy_used_candidate = calculate_path_energy(state_copy, candidate_path.nodes, charging_stations)

            # Check if depot can be reached
            energy_to_depot = state_copy.get_edge_energy_consumption(candidate_path.nodes[-1], DEFAULT_SOURCE_NODE)
            if energy_used_candidate + energy_to_depot > energy_capacity:
                station_to_add_depot = find_best_charging_station(
                    state_copy, candidate_path.nodes[-1], energy_capacity, energy_consumption, charging_stations, energy_used_candidate
                )
                if station_to_add_depot:
                    candidate_path.nodes.append(station_to_add_depot)
                    energy_used_candidate = 0
                else:
                    i += 1
                    continue

            # Ensure path ends at the depot
            if candidate_path.nodes[-1] != DEFAULT_SOURCE_NODE:
                candidate_path.nodes.append(DEFAULT_SOURCE_NODE)

            # Check demand constraint
            total_demand = state_copy.graph_api.get_total_demand_path(candidate_path.nodes)
            if total_demand > state_copy.cevrp.capacity:
                i += 1
                continue

            # Update the route with the best insertion
            updated_path = copy.deepcopy(candidate_path)
            path.nodes = updated_path.nodes
            path.path_cost = updated_path.path_cost
            path.energy = updated_path.energy
            path.demand = updated_path.demand

            # Mark node as assigned
            visited_nodes.add(node)
            unassigned_copy.pop(i)

    # Ensure all routes end at the depot
    paths_final = []
    for path in paths_copy:
        if path.nodes[-1] != DEFAULT_SOURCE_NODE:
            path.nodes.append(DEFAULT_SOURCE_NODE)
            path.path_cost = state_copy.graph_api.calculate_path_cost(path.nodes)
            energy_to_depot = state_copy.graph_api.calculate_edge_energy_consumption(
                path.nodes[-2], DEFAULT_SOURCE_NODE, energy_consumption
            )
            path.energy += energy_to_depot
        paths_final.append(copy.deepcopy(path))

    # Update the list of unassigned nodes
    unassigned_final = [node for node in state_copy.unassigned if node not in visited_nodes]

    # Return a new instance to avoid external modifications
    return CevrpState(paths_final, unassigned_final, state_copy.graph_api, state_copy.cevrp)
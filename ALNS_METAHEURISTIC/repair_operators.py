import random
from typing import Optional
from ALNS_METAHEURISTIC.solution_state import CevrpState
from Shared.config import DEFAULT_SOURCE_NODE



def find_best_charging_station(
    state: CevrpState,
    last_node: str,
    energy_capacity: float,
    energy_consumption: float,
    charging_stations: list,
    current_energy_used: float  # Add this parameter
) -> Optional[str]:
    """
    Identifies the best charging station to insert before a new node if needed.

    :param state:
    :param last_node:
    :param energy_capacity:
    :param energy_consumption:
    :param charging_stations:
    :param current_energy_used: The energy consumed so far in the current route.
    :return: The best station to insert (if necessary), otherwise None.
    """
    best_station = None
    best_station_cost = float('inf')

    for station in charging_stations:
        if station == last_node:
            return None  # If already at a charging station, no need to insert one

        # Calculate energy required to reach the station
        energy_to_station = state.graph_api.calculate_edge_energy_consumption(
            last_node, station, energy_consumption
        )

        # Check if the vehicle can reach the station with the remaining energy
        if current_energy_used + energy_to_station > energy_capacity:
            continue  # Skip if the station is not reachable

        # Calculate the cost of reaching the station
        station_cost = state.graph_api.get_edge_cost(last_node, station)

        # Track the best station (lowest cost)
        if station_cost < best_station_cost:
            best_station = station
            best_station_cost = station_cost

    return best_station

def smart_reinsertion(state: CevrpState, rnd_state: Optional[random.Random] = None) -> CevrpState:
    """
    Reinserts unassigned nodes into feasible routes while ensuring:
    - No duplicate nodes in any route.
    - Charging stations are inserted only when necessary.
    - All routes remain energy-feasible and return to the depot.
    - Returns a new CevrpState object with the updated paths.

    :return: A new CevrpState with updated paths.
    """

    # Copy the state to avoid modifying the original
    paths_copy = [path.copy() for path in state.paths]
    unassigned = state.unassigned.copy()  # Track nodes without a route
    energy_capacity = state.cevrp.energy_capacity
    energy_consumption = state.cevrp.energy_consumption  # Constant energy consumption factor
    charging_stations = state.cevrp.charging_stations

    # Track nodes already assigned to routes
    visited_nodes = set(node for path in paths_copy for node in path.nodes if node != DEFAULT_SOURCE_NODE)

    # Remove nodes already in routes from unassigned
    unassigned = [node for node in unassigned if node not in visited_nodes]

    # Iterate over each route and try to insert unassigned nodes
    for path in paths_copy:
        i = 0
        while i < len(unassigned):
            node = unassigned[i]
            if node in visited_nodes:
                i += 1
                continue  # Skip if already assigned to another route

            # **Determine the insertion position**
            if path.nodes[-1] == DEFAULT_SOURCE_NODE:
                insert_position = len(path.nodes) - 1  # Insert before the depot
            else:
                insert_position = len(path.nodes)  # Insert at the end

            # **Compute the energy consumption up to the insertion point**
            energy_used = state.graph_api.calculate_path_energy_consumption(path.nodes,energy_consumption)

            # **Check if a charging station is needed before inserting the node**
            prev_node = path.nodes[insert_position - 1]
            station_to_add = None
            if prev_node not in charging_stations:
                station_to_add = find_best_charging_station(
                    state, prev_node, energy_capacity, energy_consumption, charging_stations, energy_used
                )

            # **Create a candidate path with the node (and station, if needed) inserted**
            candidate_path = path.copy()
            if station_to_add:
                candidate_path.nodes.insert(insert_position, station_to_add)  # Insert charging station
                insert_position += 1  # Update insertion position for the node
            candidate_path.nodes.insert(insert_position, node)  # Insert the node

            # **Compute updated energy usage**
            energy_used_candidate = state.graph_api.calculate_path_energy_consumption(candidate_path.nodes,energy_consumption)

            # **Ensure the route can return to the depot**
            energy_to_depot = state.get_edge_energy_consumption(
                candidate_path.nodes[-1], DEFAULT_SOURCE_NODE
            )
            if energy_used_candidate + energy_to_depot > energy_capacity:
                # Find the best charging station to insert before returning to the depot
                last_node = candidate_path.nodes[-1]
                station_to_add_depot = find_best_charging_station(
                    state, last_node, energy_capacity, energy_consumption, charging_stations, energy_used_candidate
                )
                if station_to_add_depot:
                    candidate_path.nodes.append(station_to_add_depot)  # Insert charging station before depot
                    energy_used_candidate = 0  # Reset energy after charging
                else:
                    i += 1  # Skip if no feasible charging station found
                    continue

            # **Force the route to end at the depot**
            if candidate_path.nodes[-1] != DEFAULT_SOURCE_NODE:
                candidate_path.nodes.append(DEFAULT_SOURCE_NODE)  # Add depot at the end

            # **Check capacity constraint**
            total_demand = state.graph_api.get_total_demand_path(candidate_path.nodes)
            if total_demand > state.cevrp.capacity:
                i += 1  # Skip if demand exceeds capacity
                continue

            # **Update the current route with the best insertion**
            path.nodes = candidate_path.nodes
            path.path_cost = state.graph_api.calculate_path_cost(candidate_path.nodes)
            path.energy = energy_used_candidate
            path.demand = total_demand

            # **Mark the node as assigned**
            visited_nodes.add(node)
            unassigned.pop(i)  # Remove the node from unassigned

    # **Ensure all routes end at the depot**
    for path in paths_copy:
        if path.nodes[-1] != DEFAULT_SOURCE_NODE:
            path.nodes.append(DEFAULT_SOURCE_NODE)  # Add depot at the end

    # Update the list of unassigned nodes
    unassigned = [node for node in state.unassigned if node not in visited_nodes]

    return CevrpState(paths_copy, unassigned, state.graph_api, state.cevrp)
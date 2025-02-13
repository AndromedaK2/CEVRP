import random
from typing import Optional
from ALNS_METAHEURISTIC.solution_state import CevrpState
from Shared.config import DEFAULT_SOURCE_NODE
from Shared.path import Path


def find_best_charging_station(
    state: CevrpState,
    last_node: str,
    energy_capacity: float,
    energy_consumption: float,
    charging_stations: list,
    current_energy_used: float
) -> Optional[str]:
    """
    Identifies the best charging station to insert before a new node if needed.
    """
    best_station = None
    best_station_cost = float('inf')

    for station in charging_stations:
        if station == last_node:
            return None

        energy_to_station = state.graph_api.calculate_edge_energy_consumption(last_node, station, energy_consumption)

        if current_energy_used + energy_to_station > energy_capacity:
            continue

        station_cost = state.graph_api.get_edge_cost(last_node, station)

        if station_cost < best_station_cost:
            best_station = station
            best_station_cost = station_cost

    return best_station


def calculate_energy_usage(state: CevrpState, nodes: list, energy_consumption: float, charging_stations: list) -> float:
    """
    Calculates the total energy usage for a given path, considering resets at charging stations.
    """
    energy_used = 0
    for i in range(1, len(nodes)):
        prev_node = nodes[i - 1]
        curr_node = nodes[i]

        if prev_node in charging_stations:
            energy_used = 0

        energy_used += state.get_edge_energy_consumption(prev_node, curr_node)

    return energy_used


def insert_node_with_station(state: CevrpState, path: Path, node: str, energy_capacity: float, energy_consumption: float, charging_stations: list) -> bool:
    """
    Attempts to insert a node into the path, adding a charging station if necessary.
    """
    insert_position = len(path.nodes) - 1 if path.nodes[-1] == DEFAULT_SOURCE_NODE else len(path.nodes)
    prev_node = path.nodes[insert_position - 1]
    current_energy = calculate_energy_usage(state, path.nodes, energy_consumption, charging_stations)

    station_to_add = find_best_charging_station(state, prev_node, energy_capacity, energy_consumption, charging_stations, current_energy)

    candidate_path = path.copy()
    if station_to_add:
        candidate_path.nodes.insert(insert_position, station_to_add)
        insert_position += 1

    candidate_path.nodes.insert(insert_position, node)

    energy_after_insertion = calculate_energy_usage(state, candidate_path.nodes, energy_consumption, charging_stations)
    energy_to_depot = state.get_edge_energy_consumption(candidate_path.nodes[-1], DEFAULT_SOURCE_NODE)

    if energy_after_insertion + energy_to_depot > energy_capacity:
        depot_station = find_best_charging_station(state, candidate_path.nodes[-1], energy_capacity, energy_consumption, charging_stations, energy_after_insertion)
        if depot_station:
            candidate_path.nodes.append(depot_station)
            energy_after_insertion = 0
        else:
            return False

    total_demand = state.graph_api.get_total_demand_path(candidate_path.nodes)
    if total_demand > state.cevrp.capacity:
        return False

    candidate_path.path_cost = state.graph_api.calculate_path_cost(candidate_path.nodes)
    candidate_path.energy = energy_after_insertion
    candidate_path.demand = total_demand

    if candidate_path.nodes[-1] != DEFAULT_SOURCE_NODE:
        candidate_path.nodes.append(DEFAULT_SOURCE_NODE)

    path.nodes = candidate_path.nodes
    path.path_cost = candidate_path.path_cost
    path.energy = candidate_path.energy
    path.demand = candidate_path.demand
    return True


def smart_reinsertion(state: CevrpState, rnd_state: Optional[random.Random] = None) -> CevrpState:
    """
    Reinserts unassigned nodes into feasible routes while ensuring no duplicate nodes, proper charging station insertion,
    and valid returns to the depot.
    """
    paths_copy = [path.copy() for path in state.paths]
    paths_copy = random.sample(paths_copy, len(paths_copy))

    visited_nodes = {node for path in paths_copy for node in path.nodes if node != DEFAULT_SOURCE_NODE}
    unassigned = random.sample(state.unassigned.copy(), len(state.unassigned.copy()))
    unassigned = [node for node in unassigned if node not in visited_nodes]


    for path in paths_copy:
        i = 0
        while i < len(unassigned):
            node = unassigned[i]
            if node in visited_nodes:
                i += 1
                continue

            if insert_node_with_station(state, path, node, state.cevrp.energy_capacity, state.cevrp.energy_consumption, state.cevrp.charging_stations):
                visited_nodes.add(node)
                unassigned.pop(i)
            else:
                i += 1

    for node in unassigned:
        new_route_nodes = [DEFAULT_SOURCE_NODE, node, DEFAULT_SOURCE_NODE]
        energy_used = calculate_energy_usage(state, new_route_nodes, state.cevrp.energy_consumption, state.cevrp.charging_stations)

        if energy_used > state.cevrp.energy_capacity:
            station_to_add = find_best_charging_station(state, node, state.cevrp.energy_capacity, state.cevrp.energy_consumption, state.cevrp.charging_stations, energy_used)
            if station_to_add:
                new_route_nodes.insert(-1, station_to_add)
                energy_used = 0
            else:
                continue

        total_demand = state.graph_api.get_total_demand_path(new_route_nodes)
        if total_demand > state.cevrp.capacity:
            continue

        new_path = Path(nodes=new_route_nodes)
        new_path.path_cost = state.graph_api.calculate_path_cost(new_route_nodes)
        new_path.energy = energy_used
        new_path.demand = total_demand
        paths_copy.append(new_path)
        visited_nodes.add(node)

    unassigned = [node for node in state.unassigned if node not in visited_nodes]

    return CevrpState(paths_copy, unassigned, state.graph_api, state.cevrp)

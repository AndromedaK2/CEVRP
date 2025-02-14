import copy
import random
from typing import Optional
from ALNS_METAHEURISTIC.solution_state import CevrpState
from Shared.config import DEFAULT_SOURCE_NODE

def find_best_charging_station(state, last_node, energy_capacity, energy_consumption, charging_stations, current_energy):
    best_station = None
    best_station_cost = float('inf')
    for station in charging_stations:
        if station == last_node:
            continue
        energy_required = state.graph_api.calculate_edge_energy_consumption(last_node, station, energy_consumption)
        if current_energy + energy_required <= energy_capacity:
            cost = state.graph_api.get_edge_cost(last_node, station)
            if cost < best_station_cost:
                best_station = station
                best_station_cost = cost
    return best_station

def calculate_path_energy(state, nodes, energy_consumption, charging_stations):
    energy = 0
    for i in range(1, len(nodes)):
        if nodes[i - 1] in charging_stations:
            energy = 0
        energy += state.get_edge_energy_consumption(nodes[i - 1], nodes[i])
    return energy

def smart_reinsertion(state: CevrpState, rnd_state: Optional[random.Random] = None) -> CevrpState:

    paths = state.paths
    paths_copy = [path.copy() for path in paths]
    unassigned_copy = state.unassigned.copy()
    energy_capacity = state.cevrp.energy_capacity
    energy_consumption = state.cevrp.energy_consumption
    charging_stations = state.cevrp.charging_stations

    visited_nodes = set(node for path in paths_copy for node in path.nodes if node != DEFAULT_SOURCE_NODE)
    unassigned_copy = [node for node in unassigned_copy if node not in visited_nodes]


    for path in paths_copy:
        i = 0
        while i < len(unassigned_copy):
            node = unassigned_copy[i]
            if node in visited_nodes:
                i += 1
                continue

            insert_position = len(path.nodes) - 1 if path.nodes[-1] == DEFAULT_SOURCE_NODE else len(path.nodes)

            energy_used = calculate_path_energy(state, path.nodes, energy_consumption, charging_stations)

            prev_node = path.nodes[insert_position - 1]
            station_to_add = None
            if prev_node not in charging_stations:
                station_to_add = find_best_charging_station(
                    state, prev_node, energy_capacity, energy_consumption, charging_stations, energy_used
                )

            candidate_path = path.copy()
            if station_to_add:
                candidate_path.nodes.insert(insert_position, station_to_add)
                insert_position += 1
            candidate_path.nodes.insert(insert_position, node)

            energy_used_candidate = calculate_path_energy(state, candidate_path.nodes, energy_consumption, charging_stations)

            energy_to_depot = state.get_edge_energy_consumption(
                candidate_path.nodes[-1], DEFAULT_SOURCE_NODE
            )
            if energy_used_candidate + energy_to_depot > energy_capacity:
                station_to_add_depot = find_best_charging_station(
                    state, candidate_path.nodes[-1], energy_capacity, energy_consumption, charging_stations, energy_used_candidate
                )
                if station_to_add_depot:
                    candidate_path.nodes.append(station_to_add_depot)
                    energy_used_candidate = 0
                else:
                    i += 1
                    continue

            if candidate_path.nodes[-1] != DEFAULT_SOURCE_NODE:
                candidate_path.nodes.append(DEFAULT_SOURCE_NODE)

            total_demand = state.graph_api.get_total_demand_path(candidate_path.nodes)
            if total_demand > state.cevrp.capacity:
                i += 1
                continue

            path.nodes = candidate_path.nodes
            path.path_cost = state.graph_api.calculate_path_cost(candidate_path.nodes)
            path.energy = energy_used_candidate
            path.demand = total_demand

            visited_nodes.add(node)
            unassigned_copy.pop(i)

    unassigned_final = [node for node in unassigned_copy if node not in visited_nodes]

    return CevrpState(paths_copy, unassigned_final, state.graph_api, state.cevrp)
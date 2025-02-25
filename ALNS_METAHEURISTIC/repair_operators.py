import numpy as np
from typing import Optional

from ALNS_METAHEURISTIC.solution_state import CevrpState
from ALNS_METAHEURISTIC.repair_functions import find_best_charging_station
from Shared.config import DEFAULT_SOURCE_NODE
from Shared.path import Path

def apply_2opt(route: Path, state: CevrpState) -> Path:
    """Applies the 2-opt algorithm to optimize the given route."""
    best_route = route.copy()
    best_cost = state.graph_api.calculate_path_cost(best_route.nodes)
    for i in range(1, len(route.nodes) - 2):
        for j in range(i + 1, len(route.nodes) - 1):
            new_route = route.nodes[:i] + list(reversed(route.nodes[i:j + 1])) + route.nodes[j + 1:]
            new_cost = state.graph_api.calculate_path_cost(new_route)

            if new_cost < best_cost:
                best_route.nodes = new_route
                best_cost = new_cost

    best_route.path_cost = best_cost
    return best_route



def smart_reinsertion(state: CevrpState, rnd_state: Optional[np.random.RandomState] = None) -> CevrpState:
    """Reinserts unassigned nodes into feasible routes, ensuring constraints."""
    state_copy = state.copy()
    paths_copy = state_copy.paths
    not_feasible_paths, feasible_paths = [], []
    for path in paths_copy:
        (feasible_paths if path.feasible else not_feasible_paths).append(path)

    unassigned_copy = state_copy.unassigned
    charging_stations = state_copy.cevrp.charging_stations
    visited_nodes = {node for path in paths_copy for node in path.nodes if node != DEFAULT_SOURCE_NODE}

    unassigned_copy = [node for node in unassigned_copy if node not in visited_nodes]
    rnd_state.shuffle(unassigned_copy)

    for path in not_feasible_paths:
        i = 0
        while i < len(unassigned_copy):
            node = unassigned_copy[i]
            if node in visited_nodes:
                i += 1
                continue

            candidate_path = path.copy()
            insert_position = len(candidate_path.nodes) - 1 if candidate_path.nodes[-1] == DEFAULT_SOURCE_NODE else (
                len(candidate_path.nodes))
            energy_used = candidate_path.energy
            prev_node = path.nodes[insert_position - 1]
            energy_to_node = state_copy.get_edge_energy_consumption(prev_node, node)

            if prev_node not in charging_stations:
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
                candidate_path.nodes.insert(insert_position, node)
                candidate_path.energy = energy_to_node

            candidate_path.demand = state_copy.graph_api.get_total_demand_path(candidate_path.nodes)
            if candidate_path.demand <= state_copy.cevrp.capacity:
                path.nodes = candidate_path.nodes.copy()
                path.path_cost = state_copy.graph_api.calculate_path_cost(candidate_path.nodes)
                path.energy = candidate_path.energy
                path.demand = candidate_path.demand
                visited_nodes.add(node)
                unassigned_copy.pop(i)
            i += 1
        # Ensure all routes end at the depot
    paths_final:list[Path] = []

    for path in not_feasible_paths:
        if path.nodes[-1] != DEFAULT_SOURCE_NODE:

            current_energy = path.energy
            last_node = path.nodes[-1]

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
                        path.nodes.append(station)
                        path.energy = 0
                        energy_to_depot = state_copy.get_edge_energy_consumption(station, DEFAULT_SOURCE_NODE)
                        path.nodes.append(DEFAULT_SOURCE_NODE)
                        path.energy += energy_to_depot
                    else:
                        path.feasible = False
                        paths_final.append(path)
                        continue
                else:
                    path.nodes.append(DEFAULT_SOURCE_NODE)
                    path.energy += energy_to_depot
            else:
                energy_to_depot = state_copy.get_edge_energy_consumption(last_node, DEFAULT_SOURCE_NODE)
                path.nodes.append(DEFAULT_SOURCE_NODE)
                path.energy = energy_to_depot

        path.path_cost = state_copy.graph_api.calculate_path_cost(path.nodes)
        path.feasible = True

        path = apply_2opt(path, state_copy)
        paths_final.append(path)

    unassigned_final = [node for node in unassigned_copy if node not in visited_nodes]

    paths_final = paths_final + feasible_paths

    state_copy.graph_api.visualize_graph(paths_final, charging_stations, state_copy.cevrp.name)

    return CevrpState(
        paths=paths_final,
        unassigned=unassigned_final,
        graph_api=state_copy.graph_api,
        cevrp=state_copy.cevrp
    )
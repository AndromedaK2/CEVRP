import numpy as np
from typing import Optional

from ALNS_METAHEURISTIC.solution_state import CevrpState
from ALNS_METAHEURISTIC.repair_functions import find_best_charging_station
from Shared.config import DEFAULT_SOURCE_NODE
from Shared.path import Path




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

def adjacent_swap(state: CevrpState, rnd_state: Optional[np.random.RandomState] = None) -> CevrpState:
    """
    Applies an adjacent swap heuristic to improve routes in CEVRP, ensuring depots remain fixed.
    Iterates all customer node pairs, selects the best valid improvement.
    """
    state_copy = state.copy()
    modified_paths = []

    for path in state_copy.paths:
        original_nodes = path.nodes
        best_nodes = original_nodes.copy()
        best_cost = path.path_cost
        best_energy = path.energy

        # Iterate over customer nodes only (exclude depots at 0 and -1)
        for i in range(1, len(original_nodes) - 2):
            # Swap adjacent nodes
            new_nodes = original_nodes.copy()
            new_nodes[i], new_nodes[i + 1] = new_nodes[i + 1], new_nodes[i]

            # Calculate cost and energy
            new_cost = state_copy.graph_api.calculate_path_cost(new_nodes)
            new_energy = state_copy.calculate_path_energy(new_nodes, state_copy.cevrp.charging_stations)

            # Check if swap improves cost and respects energy
            if new_cost < best_cost and new_energy <= state_copy.cevrp.capacity:
                best_nodes = new_nodes
                best_cost = new_cost
                best_energy = new_energy

        # Update path if improvement found
        new_path = Path()
        new_path.nodes = best_nodes
        new_path.path_cost = best_cost
        new_path.energy = best_energy
        new_path.demand = path.demand  # Unchanged by swaps
        new_path.feasible = True
        modified_paths.append(new_path)
    state_copy.graph_api.visualize_graph(modified_paths, state_copy.cevrp.charging_stations, state_copy.cevrp.name)
    return CevrpState(modified_paths, state_copy.unassigned, state_copy.graph_api, state_copy.cevrp)

def general_swap(state: CevrpState, rnd_state: Optional[np.random.RandomState] = None) -> CevrpState:
    """
    Applies a general swap heuristic to improve routes in CEVRP as a repair operator.
    Swaps non-consecutive nodes in each route and keeps the best feasible improvement,
    considering energy and capacity constraints.

    :param state: The current CevrpState containing the solution.
    :param rnd_state: Random number generator state.
    :return: A new CevrpState with modified routes.
    """
    state_copy = state.copy()
    modified_paths = []

    for path in state_copy.paths:
        best_cost = state_copy.graph_api.calculate_path_cost(path.nodes)
        best_route = path.nodes[:]
        best_energy = state_copy.get_path_energy_consumption(path.nodes)

        for i in range(1, len(path.nodes) - 3):  # Exclude depot
            for j in range(i + 2, len(path.nodes) - 1):
                new_route = path.nodes[:]
                new_route[i], new_route[j] = new_route[j], new_route[i]  # Swap non-consecutive nodes
                new_cost = state_copy.graph_api.calculate_path_cost(new_route)
                new_energy = state_copy.calculate_path_energy(new_route, state_copy.cevrp.charging_stations)
                energy_valid = new_energy <= state_copy.cevrp.energy_capacity

                if new_cost < best_cost and energy_valid:
                    best_route = new_route
                    best_cost = new_cost
                    best_energy = new_energy

        # Update path with the best found solution
        new_path = Path()
        new_path.nodes = best_route
        new_path.path_cost = best_cost
        new_path.energy = best_energy
        new_path.demand = path.demand
        new_path.feasible = True
        modified_paths.append(new_path)

    state_copy.graph_api.visualize_graph(modified_paths, state_copy.cevrp.charging_stations, state_copy.cevrp.name)
    return CevrpState(modified_paths, state_copy.unassigned, state_copy.graph_api, state_copy.cevrp)

def single_insertion(state: CevrpState, rnd_state: Optional[np.random.RandomState] = None) -> CevrpState:
    """
    Applies a single insertion heuristic to improve routes in CEVRP as a repair operator.
    Removes a node and reinserts it in another position, keeping the best feasible improvement,
    considering energy and capacity constraints.

    :param state: The current CevrpState containing the solution.
    :param rnd_state: Random number generator state.
    :return: A new CevrpState with modified routes.
    """
    state_copy = state.copy()
    modified_paths = []

    for path in state_copy.paths:
        best_cost = state_copy.graph_api.calculate_path_cost(path.nodes)
        best_route = path.nodes[:]
        best_energy = state_copy.get_path_energy_consumption(path.nodes)

        for i in range(1, len(path.nodes) - 1):  # Exclude depot
            for j in range(1, len(path.nodes) - 1):
                if i != j:
                    new_route = path.nodes[:]
                    new_route.insert(j, new_route.pop(i))  # Remove and reinsert node
                    new_cost = state_copy.graph_api.calculate_path_cost(new_route)
                    new_energy = state_copy.calculate_path_energy(new_route, state_copy.cevrp.charging_stations)
                    energy_valid = new_energy <= state_copy.cevrp.energy_capacity

                    if new_cost < best_cost and energy_valid:
                        best_route = new_route
                        best_cost = new_cost
                        best_energy = new_energy

        # Update path with the best found solution
        new_path = Path()
        new_path.nodes = best_route
        new_path.path_cost = best_cost
        new_path.energy = best_energy
        new_path.demand = path.demand
        new_path.feasible = True
        modified_paths.append(new_path)
    state_copy.graph_api.visualize_graph(modified_paths, state_copy.cevrp.charging_stations, state_copy.cevrp.name)
    return CevrpState(modified_paths, state_copy.unassigned, state_copy.graph_api, state_copy.cevrp)

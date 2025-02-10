import random
from typing import Optional
from ALNS_METAHEURISTIC.solution_state import CevrpState
from Shared.config import DEFAULT_SOURCE_NODE
from Shared.path import Path


def greedy_repair(state: CevrpState,rnd_state: Optional[random.Random] = None) -> CevrpState:
    """
    Greedily reinserts unassigned nodes into the paths to minimize the cost increment.

    :param state: Current CevrpState object containing paths and unassigned nodes.
    :return: A new CevrpState with updated paths where unassigned nodes are reintegrated.
    """
    # Copy the current paths and unassigned nodes to work with
    paths = [path.copy() for path in state.paths]
    unassigned = state.unassigned[:]
    energy_consumption = state.cevrp.energy_consumption
    energy_capacity = state.cevrp.energy_capacity


    while unassigned:
        # Select the first unassigned node
        node = unassigned.pop(0)
        best_insertion_info = None
        best_cost_increase = float('inf')

        # Iterate over all paths and possible insertion points
        for path in paths:
            energy_consumed = state.graph_api.calculate_path_energy_consumption(path.nodes,energy_consumption)
            minimum_stations = state.graph_api.calculate_minimum_stations(path.nodes,energy_consumption,energy_capacity)

            for i in range(1, len(path.nodes)):
                # Retrieve the nodes at the current segment
                u, v = path.nodes[i - 1], path.nodes[i]

                # Calculate the incremental cost of inserting the node
                cost_increase = state.graph_api.calculate_segment_cost_with_insertion(u, node, v)
                new_possible_path = path.copy()
                new_possible_path.nodes.insert(i,node)
                total_demand = state.graph_api.get_total_demand_path(new_possible_path.nodes)

                # Keep track of the best insertion found
                if cost_increase < best_cost_increase and total_demand  <= state.cevrp.capacity:
                    best_cost_increase = cost_increase
                    best_insertion_info = (path, i)

        # Perform the best insertion
        if best_insertion_info:
            path, index = best_insertion_info
            path.nodes.insert(index, node)
            # Update the path cost incrementally
            path.path_cost += best_cost_increase
        else:
            # If no valid insertion was found, create a new route for the node
            new_route = Path(nodes=[DEFAULT_SOURCE_NODE, node, DEFAULT_SOURCE_NODE])
            new_route.path_cost = (
                state.graph_api.get_edge_cost(DEFAULT_SOURCE_NODE, node) +
                state.graph_api.get_edge_cost(node, DEFAULT_SOURCE_NODE)
            )
            paths.append(new_route)

    # Return the updated state
    return CevrpState(paths, [], state.graph_api, state.cevrp)


def smart_reinsertion(state: CevrpState, rnd_state: Optional[random.Random] = None) -> CevrpState:
    """
    Greedily reinserts unassigned nodes into the paths, ensuring energy constraints
    by adding charging stations when necessary.

    :param state: Current CevrpState object containing paths and unassigned nodes.
    :return: A new CevrpState with updated paths where unassigned nodes are reintegrated.
    """
    # Copy paths and unassigned nodes
    paths = [path.copy() for path in state.paths]
    unassigned = state.unassigned[:]
    energy_capacity = state.cevrp.energy_capacity
    energy_consumption = state.cevrp.energy_consumption
    charging_stations = state.cevrp.charging_stations

    while unassigned:
        node = unassigned.pop(0)
        best_insertion_info = None
        best_cost_increase = float('inf')

        for path in paths:
            for i in range(1, len(path.nodes)):
                # Nodes before and after insertion point
                u, v = path.nodes[i - 1], path.nodes[i]

                # Simulate insertion
                new_possible_path = path.copy()
                new_possible_path.nodes.insert(i, node)

                # Compute energy consumption
                energy_consumed = state.graph_api.calculate_path_energy_consumption(new_possible_path.nodes, energy_consumption)

                # Ensure feasibility: add a charging station if energy is insufficient
                if energy_consumed > energy_capacity:
                    # Find the best charging station to insert before node
                    best_station = None
                    best_station_cost = float('inf')

                    for station in charging_stations:
                        station_cost = state.graph_api.get_edge_cost(u, station) + state.graph_api.get_edge_cost(station, node)
                        if station_cost < best_station_cost:
                            best_station = station
                            best_station_cost = station_cost

                    if best_station:
                        new_possible_path.nodes.insert(i, best_station)  # Insert charging station before node
                        energy_consumed = state.graph_api.calculate_path_energy_consumption(new_possible_path.nodes)

                # Calculate cost increase and check demand constraints
                cost_increase = state.graph_api.calculate_segment_cost_with_insertion(u, node, v)
                total_demand = state.graph_api.get_total_demand_path(new_possible_path.nodes)

                if cost_increase < best_cost_increase and total_demand <= state.cevrp.capacity:
                    best_cost_increase = cost_increase
                    best_insertion_info = (path, i, best_station)

        # Perform the best insertion
        if best_insertion_info:
            path, index, best_station = best_insertion_info

            if best_station:
                path.nodes.insert(index, best_station)  # Insert station if needed
                index += 1  # Adjust index for the node insertion

            path.nodes.insert(index, node)
            path.path_cost += best_cost_increase

        else:
            # If no valid insertion was found, create a new route for the node
            new_route = Path(nodes=[DEFAULT_SOURCE_NODE, node, DEFAULT_SOURCE_NODE])
            new_route.path_cost = (
                state.graph_api.get_edge_cost(DEFAULT_SOURCE_NODE, node) +
                state.graph_api.get_edge_cost(node, DEFAULT_SOURCE_NODE)
            )
            paths.append(new_route)

    return CevrpState(paths, [], state.graph_api, state.cevrp)

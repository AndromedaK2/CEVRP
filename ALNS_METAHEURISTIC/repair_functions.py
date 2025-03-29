from typing import List

from ALNS_METAHEURISTIC.solution_state import CevrpState
from Shared.experiment import config
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
        path.energy = state.calculate_path_energy(state, path.nodes, charging_stations)  # Recalculate energy usage

    return path


def insert_charging_stations_after_each_node(state: CevrpState) -> CevrpState:
    """
    Inserts a charging station after each node in every route.
    This function modifies the input state directly and returns it.

    :param state: Current CevrpState containing paths.
    :return: The modified CevrpState instance.
    """
    charging_stations = state.cevrp.charging_stations

    for path in state.paths:
        modified_nodes = [path.nodes[0]]  # Start with the depot
        energy_used = 0  # Track energy consumption incrementally

        for i in range(1, len(path.nodes) - 1):  # Stop before the last node (depot)
            current_node = path.nodes[i]
            prev_node = modified_nodes[-1]
            modified_nodes.append(current_node)  # Add the original node

            # Compute energy consumption incrementally
            additional_energy = state.get_edge_energy_consumption(prev_node, current_node)
            energy_used += additional_energy

            # Always insert a charging station after each node if needed
            best_station = find_best_charging_station(
                state,
                current_node,
                energy_capacity=state.cevrp.energy_capacity,
                energy_consumption=state.cevrp.energy_consumption,
                charging_stations=charging_stations,
                current_energy=energy_used
            )

            if best_station:
                modified_nodes.append(best_station)  # Insert the charging station
                energy_used = 0  # Reset energy consumption after charging

        # Add the depot back at the end
        last_node = modified_nodes[-1]
        depot = path.nodes[-1]
        energy_to_depot = state.get_edge_energy_consumption(last_node, depot)
        energy_used += energy_to_depot
        modified_nodes.append(depot)

        # Update the path directly
        path.nodes[:] = modified_nodes
        path.path_cost = state.graph_api.calculate_path_cost(modified_nodes)
        path.energy = energy_used
        path.demand = state.graph_api.get_total_demand_path(modified_nodes)
        path.feasible = path.energy <= state.cevrp.energy_capacity

    return state


def create_paths(nodes: List[str], state) -> List[Path]:
    """
    Constructs multiple feasible paths using the given nodes.
    Constraints:
      - Energy limit (ensures return to DEFAULT_SOURCE_NODE)
      - Capacity limit
      - Uses charging stations to reset energy
      - Recursively assigns remaining nodes into separate paths.
    Returns:
      - A list of `Path` objects.
    """
    if not nodes:
        return []

    depot = config.default_source_node  # Ensure depot consistency
    paths: List[Path] = []  # List to store all feasible Path objects

    while nodes:
        new_path_nodes = [depot]  # Start new path at depot
        load = 0
        temp_nodes = []

        for node in nodes:
            node_demand = state.graph_api.get_demand_node(node)

            if load + node_demand > state.cevrp.capacity:
                temp_nodes.append(node)  # Save for next route
                continue

            temp_path = new_path_nodes + [node]  # Do NOT add depot yet
            energy_required = state.cevrp.get_path_energy_consumption(temp_path)

            if energy_required <= state.cevrp.energy_capacity:
                new_path_nodes.append(node)  # Add node to path
                load += node_demand
            else:
                temp_nodes.append(node)  # If energy constraint fails, leave for next path

        # Ensure the last node can return to depot
        final_path = new_path_nodes + [depot]
        return_energy_needed = state.cevrp.get_path_energy_consumption(final_path)

        if return_energy_needed <= state.cevrp.energy_capacity:
            new_path_nodes.append(depot)  # Vehicle successfully returns to depot
        else:
            if len(new_path_nodes) > 1:
                temp_nodes.append(new_path_nodes.pop(-1))  # Remove last node if return is infeasible

        # Create a Path object and store it
        path_obj = Path(
            nodes=new_path_nodes,
            path_cost=state.graph_api.calculate_path_cost(new_path_nodes),
            demand=load,
            energy=return_energy_needed,
            feasible=True
        )
        paths.append(path_obj)

        nodes = temp_nodes  # Update remaining nodes for the next path

    return paths  # ✅ Explicitly returning list of Path objects


def are_paths_depot_constrained(paths:List[Path]) -> bool:
    """
    Checks if each path starts and ends at the depot.

    :return: True if all paths start and end at the depot, False otherwise.
    """
    for path in paths:
        if not path.nodes or path.nodes[0] != config.default_source_node or path.nodes[-1] != config.default_source_node:
            return False  # Invalid path
    return True  # All paths are valid
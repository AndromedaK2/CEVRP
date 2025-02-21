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
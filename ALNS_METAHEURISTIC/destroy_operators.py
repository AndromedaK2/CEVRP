from typing import Optional

import numpy as np
from sklearn.cluster import MiniBatchKMeans

from ALNS_METAHEURISTIC.destroy_functions import is_path_valid, update_path, find_closest_customer
from ALNS_METAHEURISTIC.solution_state import CevrpState
from Shared.config import DEFAULT_SOURCE_NODE
from Shared.path import Path


def remove_overcapacity_nodes(state: CevrpState, rnd_state: Optional[np.random.RandomState] = None) -> CevrpState:
    """
    Removes nodes from paths exceeding the maximum energy capacity while ensuring a safe return to the depot.
    Charging stations reset energy consumption and recharge the battery.
    Also removes routes with only two nodes (one customer + depot).
    Prevents getting stuck by applying randomized removal of excess nodes.

    :param state: Current solution state (CevrpState).
    :param rnd_state: Random number generator state (optional).
    :return: A new CevrpState object with updated paths and unassigned nodes.
    """
    state_copy = state.copy()
    paths = state_copy.paths
    energy_capacity = state_copy.cevrp.energy_capacity
    charging_stations = set(state_copy.cevrp.charging_stations)

    if len(paths) < 2:
        raise ValueError("At least two paths are required to perform this operation.")

    unassigned = set(state_copy.unassigned)
    new_paths = []  # Store valid paths
    energy_cache = {}

    for path in paths:
        nodes = path.nodes
        num_nodes = len(nodes)
        # **Remove paths that contain only the depot and one customer**
        if num_nodes <= 3:
            unassigned.update(node for node in nodes if node != DEFAULT_SOURCE_NODE)
            continue

        energy_consumption = 0
        valid_nodes = [nodes[0]]

        for i in range(num_nodes - 1):
            current_node, next_node = nodes[i], nodes[i + 1]

            # **Reset energy at charging stations**
            if current_node in charging_stations:
                energy_consumption = 0  # Fully recharge

            # Compute additional energy needed to reach the next node
            edge = (current_node, next_node)
            if edge not in energy_cache:
                energy_cache[edge] = state_copy.get_edge_energy_consumption(current_node, next_node)
            additional_energy = energy_cache[edge]


            # **Check if the vehicle can safely reach the next node**
            if energy_consumption + additional_energy > energy_capacity:
                valid_nodes.pop(-1)
                break  # Stop before exceeding capacity

            # Add the node only if it doesn't exceed capacity
            valid_nodes.append(next_node)
            energy_consumption += additional_energy

        # Nodes that couldn't be added
        remaining_nodes = nodes[len(valid_nodes):]
        # **Filter out charging stations from unassigned nodes**
        unassigned.update(node for node in remaining_nodes if node != DEFAULT_SOURCE_NODE and node not in charging_stations)

        # **Recalculate cost, demand, and energy**
        if len(valid_nodes) > 1:
            valid_path = Path()
            valid_path.nodes = valid_nodes
            valid_path.path_cost = state_copy.graph_api.calculate_path_cost(valid_nodes)
            valid_path.demand = state_copy.graph_api.get_total_demand_path(valid_nodes)
            valid_path.energy = energy_consumption
            valid_path.feasible = (
                valid_nodes[0] == DEFAULT_SOURCE_NODE
                and valid_nodes[-1] == DEFAULT_SOURCE_NODE
                and len(valid_nodes) > 2
            )
            new_paths.append(valid_path)

    # **Filter out charging stations from the final unassigned list**
    unassigned = list(unassigned - charging_stations)
    state_copy.graph_api.visualize_graph(new_paths, charging_stations, state_copy.cevrp.name)
    return CevrpState(new_paths, unassigned, state_copy.graph_api, state_copy.cevrp)


def remove_charging_station(state: CevrpState, rnd_state: Optional[np.random.RandomState] = None) -> CevrpState:
    """
    Randomly removes one instance of a duplicated charging station from a route
    while keeping the energy constraint valid.

    :param state: The current CevrpState containing the solution.
    :param rnd_state: Random number generator state.
    :return: A new CevrpState with modified routes.
    """
    state_copy = state.copy()
    modified_paths = []

    for path in state_copy.paths:
        station_positions = [i for i, node in enumerate(path.nodes) if node in state_copy.cevrp.charging_stations]

        if len(station_positions) < 2:
            # No duplicated charging stations, keep the path unchanged
            modified_paths.append(path)
            continue

        # Select a charging station instance to remove
        index_to_remove = rnd_state.choice(station_positions) if rnd_state else np.random.choice(station_positions)
        removed_station = path.nodes[index_to_remove]

        # Ensure removing the station does not break a critical connection
        if 0 < index_to_remove < len(path.nodes) - 1:
            prev_node = path.nodes[index_to_remove - 1]
            next_node = path.nodes[index_to_remove + 1]

            # Check if the neighboring nodes can still be connected
            if not state_copy.graph_api.has_edge(prev_node, next_node):
                # If no direct edge exists between neighbors, keep the station
                modified_paths.append(path)
                continue

        # Remove the charging station
        modified_nodes = path.nodes[:index_to_remove] + path.nodes[index_to_remove + 1:]

        # Recalculate energy consumption and validate feasibility
        energy_used = 0
        feasible = True
        for i in range(len(modified_nodes) - 1):
            current_node, next_node = modified_nodes[i], modified_nodes[i + 1]

            # Reset energy if the current node is a charging station
            if current_node in state_copy.cevrp.charging_stations:
                energy_used = 0

            energy_used += state_copy.get_edge_energy_consumption(current_node, next_node)

            # If the energy constraint is violated, keep the original path
            if energy_used > state_copy.cevrp.energy_capacity:
                feasible = False
                break

        # Ensure the path remains connected after the removal
        if not state_copy.graph_api.is_path_connected(modified_nodes):
            modified_paths.append(path)  # Keep the original path if connectivity is lost
            continue

        # If removal is feasible, update the path
        if feasible:
            new_path = Path()
            new_path.nodes = modified_nodes
            new_path.path_cost = state_copy.graph_api.calculate_path_cost(modified_nodes)
            new_path.energy = energy_used
            new_path.demand = state_copy.graph_api.get_total_demand_path(modified_nodes)
            new_path.feasible = True
            modified_paths.append(new_path)
        else:
            modified_paths.append(path)  # Keep the original path if energy feasibility is not met

    # Visualize the graph before and after the removal
    state_copy.graph_api.visualize_graph(state_copy.paths, state_copy.cevrp.charging_stations,
                                         f"Before Remove-Charging-Station {state_copy.cevrp.name}")
    state_copy.graph_api.visualize_graph(modified_paths, state_copy.cevrp.charging_stations,
                                         f"After Remove-Charging-Station {state_copy.cevrp.name}")

    return CevrpState(modified_paths, state_copy.unassigned, state_copy.graph_api, state_copy.cevrp, state)


def worst_removal(state: CevrpState, rng: Optional[np.random.RandomState] = None) -> CevrpState:
    """
    Removes the worst (most costly) customer nodes while preserving depots and charging stations.
    Removed nodes are stored in `state_copy.unassigned` along with their route index.
    """
    removal_fraction = 0.2
    state_copy = state.copy()
    candidate_nodes = []

    # Identify removable nodes (exclude depots and charging stations)
    for route_idx, path in enumerate(state_copy.paths):  # Track route index
        for i in range(1, len(path.nodes) - 1):  # Skip first/last node (depots)
            node = path.nodes[i]

            original_cost = path.path_cost  # Calculate removal cost savings
            new_path = path.nodes[:i] + path.nodes[i + 1:]
            new_cost = state_copy.graph_api.calculate_path_cost(new_path)
            removal_cost = original_cost - new_cost  # Higher = better to remove

            # Store node, removal cost, and its route index
            candidate_nodes.append((node, removal_cost, route_idx))

    # Sort by descending removal cost and select top 20%
    candidate_nodes.sort(key=lambda x: x[1], reverse=True)
    num_to_remove = int(len(candidate_nodes) * removal_fraction)
    nodes_to_remove = [(node, route_idx) for node, _, route_idx in candidate_nodes[:num_to_remove]]

    # Update paths while preserving depots
    modified_paths = []
    for route_idx, path in enumerate(state_copy.paths):
        # Remove only nodes that belong to this route
        new_nodes = [n for n in path.nodes if (n, route_idx) not in nodes_to_remove]

        # Energy feasibility check
        new_energy = state_copy.calculate_path_energy(new_nodes, state_copy.cevrp.charging_stations)
        if new_energy > state_copy.cevrp.energy_capacity:
            modified_paths.append(path)  # Keep original if infeasible
        else:
            # Create new path with updated metrics
            new_cost = state_copy.graph_api.calculate_path_cost(new_nodes)
            new_demand = state_copy.graph_api.get_total_demand_path(new_nodes)
            modified_paths.append(Path(
                nodes=new_nodes,
                path_cost=new_cost,
                energy=new_energy,
                demand=new_demand,
                feasible=True
            ))

    # Update unassigned list
    for node, _ in nodes_to_remove:
        state_copy.unassigned.append(node)

    state_copy.graph_api.visualize_graph(modified_paths, state_copy.cevrp.charging_stations,
                                         f"After Worst-Removal {state_copy.cevrp.name}")

    return CevrpState(modified_paths,state_copy.unassigned,state_copy.graph_api,state_copy.cevrp,state)


def cluster_removal(state: CevrpState, rng: Optional[np.random.RandomState] = None) -> CevrpState:
    """
    Removes customers in geographic clusters, ensuring route feasibility post-removal.
    """
    # Initialize appropriate RNG type
    if rng is None:
        rng = np.random.default_rng()  # Modern Generator

    kmeans_seed = rng.integers(0, 2**32 - 1)

    delta = 5  # Max nodes to remove; adjust based on problem size if needed
    state_copy = state.copy()
    modified_paths = [path.copy() for path in state_copy.paths]  # Ensure deep copy if needed
    removed_nodes = []

    # Step 1: Select initial route with sufficient customers
    candidate_routes = [p for p in modified_paths if len(p.nodes) > 3 and
                        any(node not in state_copy.cevrp.charging_stations and node != DEFAULT_SOURCE_NODE
                            for node in p.nodes)]
    if not candidate_routes:
        return state

    selected_path = rng.choice(candidate_routes)
    customers = [n for n in selected_path.nodes if
                 n not in state_copy.cevrp.charging_stations and n != DEFAULT_SOURCE_NODE]

    if len(customers) < 2:
        return state

    # Step 2: Adaptive clustering based on customer count
    n_clusters = min(2, len(customers))  # Ensure clusters <= customer count
    coordinates = np.array([state_copy.graph_api.get_node_coordinates(c) for c in customers])

    # Use MiniBatchKMeans for efficiency with large datasets
    kmeans = MiniBatchKMeans(n_clusters=min(2, len(customers)),
                             random_state=kmeans_seed).fit(coordinates)

    clusters = [[] for _ in range(n_clusters)]
    for i, label in enumerate(kmeans.labels_):
        clusters[label].append(customers[i])

    # Select largest cluster for removal to maximize impact
    selected_cluster = max(clusters, key=len)
    to_remove = rng.choice(selected_cluster, size=min(delta, len(selected_cluster)), replace=False)
    removed_nodes.extend(to_remove)

    # Update path and validate feasibility
    new_nodes = [n for n in selected_path.nodes if n not in to_remove]
    if not is_path_valid(new_nodes, state_copy):
        return state  # Abort if removal breaks feasibility
    update_path(selected_path, new_nodes, state_copy)

    # Step 3: Expand removal to nearby routes if needed
    while len(removed_nodes) < delta:
        # Find the closest customer in other routes to any removed node
        closest = find_closest_customer(removed_nodes, modified_paths, state_copy)
        if not closest:
            break

        target_route = closest['route']
        customers = [n for n in target_route.nodes if
                     n not in state_copy.cevrp.charging_stations and n != DEFAULT_SOURCE_NODE]
        if len(customers) < 2:
            break

        # Re-cluster target route's customers
        n_clusters = min(2, len(customers))
        coordinates = np.array([state_copy.graph_api.get_node_coordinates(c) for c in customers])
        kmeans = MiniBatchKMeans(n_clusters=n_clusters, random_state=kmeans_seed).fit(coordinates)
        clusters = [[] for _ in range(n_clusters)]
        for i, label in enumerate(kmeans.labels_):
            clusters[label].append(customers[i])

        selected_cluster = max(clusters, key=len)
        add_remove = rng.choice(selected_cluster,
                                size=min(delta - len(removed_nodes), len(selected_cluster)),
                                replace=False)
        removed_nodes.extend(add_remove)

        new_nodes = [n for n in target_route.nodes if n not in add_remove]
        if not is_path_valid(new_nodes, state_copy):
            break
        update_path(target_route, new_nodes, state_copy)

    # Step 4: Cleanup empty paths and update state
    modified_paths = [p for p in modified_paths if len(p.nodes) > 2]  # Remove depot-only paths
    state_copy.unassigned.extend(removed_nodes)
    state_copy.graph_api.visualize_graph(modified_paths, state_copy.cevrp.charging_stations,
                                         f"After Cluster-Removal {state_copy.cevrp.name}")
    return CevrpState(modified_paths, state_copy.unassigned, state_copy.graph_api, state_copy.cevrp, state )



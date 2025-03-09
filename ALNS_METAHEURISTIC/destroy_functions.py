from typing import List, Optional
from scipy.spatial import distance

from ALNS_METAHEURISTIC.solution_state import CevrpState
from Shared.config import config
from Shared.path import Path


def is_path_valid(nodes: List[str], state: CevrpState) -> bool:
    """Check energy, demand, and structural feasibility."""
    if nodes[0] != config.default_source_node or nodes[-1] != config.default_source_node:
        return False
    demand = state.graph_api.get_total_demand_path(nodes)
    if demand > state.cevrp.capacity:
        return False
    energy = state.calculate_path_energy(nodes, state.cevrp.charging_stations)
    return energy <= state.cevrp.energy_capacity


def update_path(path: Path, new_nodes: List[str], state: CevrpState) -> None:
    """Update path data and feasibility status."""
    path.nodes = new_nodes
    path.demand = state.graph_api.get_total_demand_path(new_nodes)
    path.energy = state.calculate_path_energy(new_nodes, state.cevrp.charging_stations)
    path.path_cost = state.graph_api.calculate_path_cost(new_nodes)
    path.feasible = is_path_valid(new_nodes, state)


def find_closest_customer(removed_nodes: List[str], paths: List[Path], state: CevrpState) -> Optional[dict]:
    """Find the closest customer in other routes to any removed node."""
    closest = None
    for removed in removed_nodes:
        coord = state.graph_api.get_node_coordinates(removed)
        for path in paths:
            if path.nodes == [config.default_source_node]:  # Skip depot-only
                continue
            for node in path.nodes:
                if node in state.cevrp.charging_stations or node == config.default_source_node:
                    continue
                node_coord = state.graph_api.get_node_coordinates(node)
                dist = distance.euclidean(coord, node_coord)
                if not closest or dist < closest['distance']:
                    closest = {'node': node, 'route': path, 'distance': dist}
    return closest
from Shared.graph_api import GraphApi
from Shared.path import Path


def apply_2opt(path: Path, graph_api:GraphApi) -> Path:
    """Applies the 2-opt algorithm to optimize the given route."""
    best_route = path.copy()
    best_cost = path.path_cost
    for i in range(1, len(path.nodes) - 1):
        for j in range(i + 1, len(path.nodes) - 1):
            new_route = path.nodes[:i] + list(reversed(path.nodes[i:j + 1])) + path.nodes[j + 1:]
            new_cost = graph_api.calculate_path_cost(new_route)
            if new_cost < best_cost:
                best_route.nodes = new_route
                best_cost = new_cost
    best_route.path_cost = best_cost
    return best_route
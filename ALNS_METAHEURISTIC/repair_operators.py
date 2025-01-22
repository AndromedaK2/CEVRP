from ALNS_METAHEURISTIC.solution_state import CevrpState
from Shared.graph_api import GraphApi

def calculate_path_cost(graph_api: GraphApi, nodes: list[str]) -> float:
    """
    Calculates the total cost of a path based on the edges in the graph.

    :param graph_api: An instance of GraphApi for accessing edge costs.
    :param nodes: List of nodes in the path.
    :return: The total cost of the path.
    """
    cost = 0.0
    for i in range(len(nodes) - 1):
        cost += graph_api.get_edge_cost(nodes[i], nodes[i + 1])
    return cost

def greedy_repair(graph_api: GraphApi, state: CevrpState) -> CevrpState:
    """
    Greedily reinserts unassigned nodes into the paths to minimize the cost increment.

    :param graph_api: An instance of GraphApi for accessing graph-related methods.
    :param state: Current CevrpState object containing paths and unassigned nodes.
    :return: A new CevrpState with updated paths where unassigned nodes are reintegrated.
    """
    # Copy the current paths and unassigned nodes to work with
    paths = [path.copy() for path in state.paths]
    unassigned = state.unassigned[:]

    while unassigned:
        # Select the first unassigned node
        node = unassigned.pop(0)
        best_insertion = None
        best_cost_increase = float('inf')

        # Iterate over all paths and possible insertion points
        for path in paths:
            for i in range(1, len(path.nodes)):
                # Retrieve the nodes at the current segment
                u, v = path.nodes[i - 1], path.nodes[i]

                # Calculate the incremental cost of inserting the node
                cost_increase = graph_api.calculate_segment_cost_with_insertion(u, node, v)

                # Keep track of the best insertion found
                if cost_increase < best_cost_increase:
                    best_cost_increase = cost_increase
                    best_insertion = (path, i)

        # Perform the best insertion
        if best_insertion:
            path, index = best_insertion
            path.nodes.insert(index, node)
            # Recalculate the path cost after the insertion
            path.path_cost = calculate_path_cost(graph_api, path.nodes)

    # Return the updated state
    return CevrpState(paths, [])

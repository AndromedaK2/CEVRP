import random
from typing import Optional
from ALNS_METAHEURISTIC.solution_state import CevrpState


def greedy_repair(state: CevrpState,rnd_state: Optional[random.Random] = None) -> CevrpState:
    """
    Greedily reinserts unassigned nodes into the paths to minimize the cost increment.

    :param state: Current CevrpState object containing paths and unassigned nodes.
    :return: A new CevrpState with updated paths where unassigned nodes are reintegrated.
    """
    # Copy the current paths and unassigned nodes to work with
    paths = [path.copy() for path in state.paths]
    unassigned = state.unassigned[:]

    while unassigned:
        # Select the first unassigned node
        node = unassigned.pop(0)
        best_insertion_info = None
        best_cost_increase = float('inf')

        # Iterate over all paths and possible insertion points
        for path in paths:
            for i in range(1, len(path.nodes)):
                # Retrieve the nodes at the current segment
                u, v = path.nodes[i - 1], path.nodes[i]

                # Calculate the incremental cost of inserting the node
                cost_increase = state.graph_api.calculate_segment_cost_with_insertion(u, node, v)

                # Keep track of the best insertion found
                if cost_increase < best_cost_increase and state.graph_api.get_total_demand_path(path.nodes) < state.cevrp.capacity:
                    best_cost_increase = cost_increase
                    best_insertion_info = (path, i)

        # Perform the best insertion
        if best_insertion_info:
            path, index = best_insertion_info
            path.nodes.insert(index, node)
            # Update the path cost incrementally
            path.path_cost += best_cost_increase

    # Return the updated state
    return CevrpState(paths, [], state.graph_api, state.cevrp)
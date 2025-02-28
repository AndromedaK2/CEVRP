from typing import List

from ALNS_METAHEURISTIC.destroy_operators import remove_charging_station
from ALNS_METAHEURISTIC.make_alns import make_alns
from ALNS_METAHEURISTIC.repair_operators import adjacent_swap, general_swap, single_insertion
from ALNS_METAHEURISTIC.solution_state import CevrpState
from Shared.config import INSTANCE_FILES, DEFAULT_SOURCE_NODE, NUM_ANTS, MAX_ANT_STEPS, NUM_ITERATIONS
from Shared.graph_api import GraphApi
from Shared.heuristic import apply_2opt
from Shared.path import Path
from Shared.coordinates_manager import CoordinatesManager
from MMAS.aco import ACO
from Shared.cevrp import CEVRP


def select_instance(instance_files: List[str]) -> str:
    """Prompts the user to select an instance file."""
    print("Select an instance by entering its number:")
    for idx, file_path in enumerate(instance_files):
        print(f"{idx + 1}: {file_path}")
    while True:
        try:
            selection = int(input("Enter the number of the instance: ")) - 1
            if 0 <= selection < len(instance_files):
                return instance_files[selection]
            print("Invalid selection. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def create_cevrp_instance(file_path: str) -> CEVRP:
    """Parses and creates a CEVRP instance from the selected file path."""
    try:
        cevrp = CEVRP.parse_evrp_instance_from_file(file_path, include_stations=False)
        print(f"Instance successfully created from: {file_path}")
        return cevrp
    except Exception as e:
        print(f"Error creating instance from: {file_path}, Error: {e}")
        exit(1)


def format_path(paths: List[Path]) -> str:
    """Formats and returns a string representation of routes."""
    header = ("\n".join([
        "╔════════════════════════════════════════╗",
        "║               Found Routes             ║",
        "╚════════════════════════════════════════╝"
    ]))

    formatted_routes = [header]
    for idx, path in enumerate(paths, start=1):
        route_str = " -> ".join(path.nodes)
        formatted_routes.append(f"► Route {idx}: {route_str}\n  Cost: {path.path_cost:.2f}")
        formatted_routes.append("-----------------------------------------")

    return "\n".join(formatted_routes)


def solve_with_aco(cevrp: CEVRP) -> tuple:
    """Solves the instance using ACO and returns the computed paths and cost."""

    # Step 1: Build the graph
    manager = CoordinatesManager(cevrp.node_coord_section)
    manager.compute_distances()
    graph = manager.build_graph()

    # Step 2: Initialize ACO
    aco = ACO(
        graph,
        max_ant_steps=MAX_ANT_STEPS,
        num_iterations=NUM_ITERATIONS,
        best_path_cost=cevrp.optimal_value,
        cevrp=cevrp,
        use_route_construction=False  # Ensure this setting is correct
    )

    # Step 3: Solve the ACO routing problem
    flatten_paths, initial_cost, paths = aco.find_shortest_path(
        start=DEFAULT_SOURCE_NODE,
        num_ants=NUM_ANTS
    )

    # Step 4: Apply 2-opt optimization
    new_paths = [apply_2opt(path, aco.graph_api) for path in paths]

    # Step 5: Compute optimized cost only if paths changed
    optimized_cost = aco.graph_api.calculate_paths_cost(new_paths) if new_paths != paths else initial_cost

    return (flatten_paths, optimized_cost, new_paths), aco.graph_api

def solve_with_alns(paths: List[Path], cevrp: CEVRP) -> tuple:
    """Applies ALNS to improve the routes found by ACO."""
    cevrp.add_charging_stations_to_nodes()
    manager = CoordinatesManager(cevrp.node_coord_section)
    manager.compute_distances()
    graph = manager.build_graph()
    graph_api = GraphApi(graph)

    cevrp_state = CevrpState(paths, graph_api=graph_api, cevrp=cevrp)
    return make_alns(
        cevrp_state,
        destroy_operators=[remove_charging_station],
        repair_operators=[adjacent_swap, general_swap, single_insertion],
    ), graph_api


if __name__ == '__main__':
    selected_file = select_instance(INSTANCE_FILES)
    print(f"Selected instance: {selected_file}")

    cevrp_instance = create_cevrp_instance(selected_file)

    # Solve using ACO
    (aco_flatten_paths, aco_cost, aco_paths), aco_graph_api = solve_with_aco(cevrp_instance)
    print(f"ACO - Initial routes:\n{format_path(aco_paths)}")
    print(f"ACO - Initial total cost: {aco_cost}")
    aco_graph_api.visualize_graph(aco_paths, cevrp_instance.charging_stations, cevrp_instance.name)

    # Apply ALNS
    (best_state, best_cost, best_paths, unassigned_nodes), alns_graph_api = solve_with_alns(aco_paths, cevrp_instance)
    print(f"ALNS - Final routes:\n{format_path(best_paths)}")
    print(f"ALNS - Final total cost: {best_cost}")
    alns_graph_api.visualize_graph(best_paths, cevrp_instance.charging_stations, cevrp_instance.name)
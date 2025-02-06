from typing import List

from ALNS_METAHEURISTIC.destroy_operators import random_destroy
from ALNS_METAHEURISTIC.make_alns import make_alns
from ALNS_METAHEURISTIC.repair_operators import greedy_repair
from ALNS_METAHEURISTIC.solution_state import CevrpState
from Shared.config import INSTANCE_FILES, DEFAULT_SOURCE_NODE, NUM_ANTS, MAX_ANT_STEPS, NUM_ITERATIONS
from Shared.path import Path
from Shared.coordinates_demand_manager import CoordinatesDemandManager
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
    """
    Formats the paths with a nicer, decorated style.
    Example output:
    ╔════════════════════════════════════════╗
    ║               Found Routes             ║
    ╚════════════════════════════════════════╝
    ► Route 1: 1 -> 2 -> 3 -> 4
      Cost: 10.50
    -----------------------------------------
    ► Route 2: 1 -> 5 -> 6 -> 7
      Cost: 15.80
    -----------------------------------------
    ► Route 3: 1 -> 8 -> 9 -> 10
      Cost: 20.75
    -----------------------------------------
    """
    header = "╔════════════════════════════════════════╗\n" \
             "║               Found Routes             ║\n" \
             "╚════════════════════════════════════════╝"

    formatted_routes = [header]
    for idx, path in enumerate(paths, start=1):
        route_str = " -> ".join(path.nodes)  # Join the nodes with '->'
        formatted_routes.append(f"► Route {idx}: {route_str}\n  Cost: {path.path_cost:.2f}")
        formatted_routes.append("-----------------------------------------")

    return "\n".join(formatted_routes)

if __name__ == '__main__':
    # Instance selection
    selected_file = select_instance(INSTANCE_FILES)
    print(f"Selected instance: {selected_file}")

    # Create CEVRP instance
    cevrp_instance = create_cevrp_instance(selected_file)
    manager = CoordinatesDemandManager(cevrp_instance.node_coord_section)
    manager.compute_distances()
    graph = manager.build_graph()

    # Solve using ACO
    aco = ACO(
        graph,
        max_ant_steps=MAX_ANT_STEPS,
        num_iterations=NUM_ITERATIONS,
        best_path_cost=cevrp_instance.optimal_value,
        cevrp=cevrp_instance,
        use_route_construction=False
    )
    aco_flatten_paths, aco_cost, aco_paths = aco.find_shortest_path(
        start=DEFAULT_SOURCE_NODE,
        num_ants=NUM_ANTS,
    )

    # Format and display initial routes
    formatted_paths = format_path(aco_paths)
    print(f"ACO - Initial routes:\n{formatted_paths}")
    print(f"ACO - Initial total cost: {aco_cost}")
    aco.graph_api.visualize_graph(aco_paths, cevrp_instance.name)

    # Apply ALNS operators
    cevrp_state = CevrpState(aco_paths, graph_api=aco.graph_api, cevrp=cevrp_instance)
    best_state, best_cost, best_paths, unassigned_nodes = make_alns(
        cevrp_state,
        destroy_operators=[random_destroy],
        repair_operators=[greedy_repair],
    )

    # Format and display final routes
    formatted_paths = format_path(best_paths)
    print(f"ALNS - Final routes:\n{formatted_paths}")
    print(f"ALNS - Final total cost: {best_cost}")

    # Visualize the final routes
    aco.graph_api.visualize_graph(best_paths, cevrp_instance.name)
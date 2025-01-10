from typing import List

from Shared.path import Path
from Shared.coordinates_demand_manager import CoordinatesDemandManager
from MMAS.aco import ACO
from Shared.cevrp import CEVRP

# Constant for instance files
INSTANCE_FILES: List[str] = [
    "Shared/Instances/E-n22-k4.evrp",
    "Shared/Instances/E-n23-k3.evrp",
    "Shared/Instances/E-n30-k3.evrp",
    "Shared/Instances/E-n33-k4.evrp",
    "Shared/Instances/E-n51-k5.evrp",
    "Shared/Instances/E-n76-k7.evrp",
    "Shared/Instances/E-n101-k8.evrp",
    "Shared/Instances/X-n143-k7.evrp",
    "Shared/Instances/X-n214-k11.evrp",
    "Shared/Instances/X-n351-k40.evrp",
    "Shared/Instances/X-n459-k26.evrp",
    "Shared/Instances/X-n573-k30.evrp",
    "Shared/Instances/X-n685-k75.evrp",
    "Shared/Instances/X-n749-k98.evrp",
    "Shared/Instances/X-n819-k171.evrp",
    "Shared/Instances/X-n916-k207.evrp",
    "Shared/Instances/X-n1001-k43.evrp"
]
DEFAULT_SOURCE_NODE: str = "1"
NUM_ANTS: int = 100
MAX_ANT_STEPS: int = 100
NUM_ITERATIONS: int = 100


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
        cevrp = CEVRP.parse_evrp_instance_from_file(file_path)
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
    # Select an instance
    selected_file = select_instance(INSTANCE_FILES)
    print(f"Selected instance: {selected_file}")

    # Create CEVRP instance and manage coordinates
    cevrp_instance = create_cevrp_instance(selected_file)
    manager = CoordinatesDemandManager(cevrp_instance.node_coord_section)
    manager.compute_distances()
    graph = manager.build_graph()

    # Solve using ACO
    aco = ACO(graph, max_ant_steps=MAX_ANT_STEPS, num_iterations=NUM_ITERATIONS,
              best_path_cost=cevrp_instance.optimal_value, cevrp=cevrp_instance)
    aco_flatten_paths, aco_cost, aco_paths = aco.find_shortest_path(
        start=DEFAULT_SOURCE_NODE,
        num_ants=NUM_ANTS,
    )
    # Format and print routes
    formatted_paths = format_path(aco_paths)
    print(f"ACO - Found routes:\n{formatted_paths}")
    print(f"ACO - Total cost: {aco_cost}")
    # Benchmark and visualization
    aco.graph_api.visualize_graph(aco_paths, cevrp_instance.name)
    cevrp_instance.get_benchmark()
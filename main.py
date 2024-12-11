from typing import List
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

    # Benchmark and visualization
    aco.graph_api.visualize_graph(aco_paths, cevrp_instance.name)
    cevrp_instance.get_benchmark()
    print(f"ACO - path: {aco_flatten_paths}, cost: {aco_cost}")

from typing import List

from Shared.benchmark import get_benchmark
from Shared.coordinates_demand_manager import CoordinatesDemandManager
from MMAS.aco import ACO
from Shared.cevrp import CEVRP

if __name__ == '__main__':
    # List of instance files
    instance_files: List[str] = [
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

    # Prompt user to select an instance
    print("Select an instance by entering its number:")
    for idx, file_path in enumerate(instance_files):
        print(f"{idx + 1}: {file_path}")

    while True:
        try:
            selection = int(input("Enter the number of the instance: ")) - 1
            if 0 <= selection < len(instance_files):
                selected_file = instance_files[selection]
                break
            else:
                print("Invalid selection. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    print(f"Selected instance: {selected_file}")

    # Create the selected EVRP instance
    try:
        cevrp = CEVRP.parse_evrp_instance_from_file(selected_file)
        print(f"Instance successfully created from: {selected_file}")
    except Exception as e:
        print(f"Error creating instance from: {selected_file}, Error: {e}")
        exit(1)

    # Coordinates and graph manager
    manager = CoordinatesDemandManager(cevrp.node_coord_section)
    manager.calculate_distances()
    G = manager.create_graph_from_manager()

    # ACO solver
    aco = ACO(G, ant_max_steps=100, num_iterations=100, best_path_cost=cevrp.optimal_value,
              cevrp=cevrp)
    source:str =  "1"
    aco_path, aco_cost = aco.find_shortest_path(
        source,
        num_ants=10,
    )

    # Benchmark and visualization
    get_benchmark()
    aco.graph_api.visualize_graph(aco_path)

    print(f"ACO - path: {aco_path}, cost: {aco_cost}")

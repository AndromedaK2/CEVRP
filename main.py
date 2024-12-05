import numpy as np

from Shared.benchmark import get_benchmark
from Shared.coordinates_demand_manager import CoordinatesDemandManager
from MMAS.aco import ACO
from Shared.evrp import EVRP

if __name__ == '__main__':


    file_path = "Shared/Instances/E-n22-k4.evrp"
    evrp_instance = EVRP.parse_evrp_instance_from_file(file_path)

    manager = CoordinatesDemandManager(evrp_instance.node_coord_section)
    manager.calculate_distances()

    G = manager.create_graph_from_manager()

    aco = ACO(G, ant_max_steps=100, num_iterations=100)
    source = "1"
    aco_path, aco_cost = aco.find_shortest_path(
        source,
        num_ants=4
    )

    get_benchmark()

    aco.graph_api.visualize_graph(aco_path)

    print(f"ACO - path: {aco_path}, cost: {aco_cost}")
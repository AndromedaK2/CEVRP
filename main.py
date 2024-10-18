import numpy as np

from CVRP.coordinates_demand_manager import CoordinatesDemandManager
from MMAS.aco import ACO

if __name__ == '__main__':
    # Define the coordinates and demand
    data = np.array([
        [1, 145, 215, 0],  # Depósito (demanda 0)
        [2, 151, 264, 1100],
        [3, 159, 261, 700],
        [4, 130, 254, 800],
        [5, 128, 252, 1400],
        [6, 163, 247, 2100],
        [7, 146, 246, 400],
        [8, 161, 242, 800],
        [9, 142, 239, 100],
        [10, 163, 236, 500],
        [11, 148, 232, 600],
        [12, 128, 231, 1200],
        [13, 156, 217, 1300],
        [14, 129, 214, 1300],
        [15, 146, 208, 300],
        [16, 164, 208, 900],
        [17, 141, 206, 2100],
        [18, 147, 193, 1000],
        [19, 164, 193, 900],
        [20, 129, 189, 2500],
        [21, 155, 185, 1800],
        [22, 139, 182, 700],
        [23, 137, 193, 0],  # Estación de carga (demanda 0)
        [24, 137, 213, 0],  # Estación de carga (demanda 0)
        [25, 137, 234, 0],  # Estación de carga (demanda 0)
        [26, 137, 254, 0],  # Estación de carga (demanda 0)
        [27, 155, 193, 0],  # Estación de carga (demanda 0)
        [28, 155, 213, 0],  # Estación de carga (demanda 0)
        [29, 155, 234, 0],  # Estación de carga (demanda 0)
        [30, 155, 254, 0]  # Estación de carga (demanda 0)
    ])

    manager = CoordinatesDemandManager(data)
    manager.calculate_distances()

    G = manager.create_graph_from_manager()

    aco = ACO(G, ant_max_steps=100, num_iterations=100, ant_random_spawn=True)
    source = "1"
    destination = "5"
    aco_path, aco_cost = aco.find_shortest_path(
        source,
        destination,
        num_ants=100,
    )

    print(f"ACO - path: {aco_path}, cost: {aco_cost}")
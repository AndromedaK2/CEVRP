import time
from typing import List

from ALNS_METAHEURISTIC.destroy_operators import remove_charging_station, worst_removal, cluster_removal
from ALNS_METAHEURISTIC.make_alns import make_alns
from ALNS_METAHEURISTIC.repair_operators import greedy_insertion, regret_k_insertion, best_feasible_insertion
from ALNS_METAHEURISTIC.solution_state import CevrpState
from Shared.config import config
from Shared.Utils.exceptions import NoSolutionFoundError
from Shared.graph_api import GraphApi
from Shared.heuristic import apply_2opt, apply_2opt_star, apply_node_shift
from Shared.path import Path
from Shared.Utils.coordinates_manager import CoordinatesManager
from MMAS.aco import ACO
from Shared.cevrp import CEVRP


def select_instance(instance_files: List[str]) -> str:
    """Prompts the user to select an instance file from a list."""
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
        print(f"✅ Instance successfully created from: {file_path}")
        return cevrp
    except FileNotFoundError:
        raise FileNotFoundError(f"❌ File {file_path} not found.")
    except Exception as exception:
        raise RuntimeError(f"❌ Error creating instance from {file_path}: {exception}")


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
        formatted_routes.append(f"► Route {idx}: {route_str}\n  Cost: {path.path_cost}")
        formatted_routes.append("-----------------------------------------")

    return "\n".join(formatted_routes)


def compute_execution_params(instance_name: str) -> tuple:
    """
    Compute the execution time (ExeTime) in minutes, along with max_no_improve,
    based on the instance name and number of nodes.

    Parameters:
        instance_name (str): Name of the instance, e.g., 'Shared/Instances/E-n22-k4.evrp'.

    Returns:
        tuple: (exe_time_minutes, max_no_improve)
    """
    # Extract the instance identifier (e.g., 'E-n22-k4')
    instance_id = instance_name.split('/')[-1].replace('.evrp', '')

    # Extract numerical part from instance name
    dimension = int(instance_id.split('-')[1][1:])

    # Determine problem category and theta value
    if 22 <= dimension <= 101:
        theta = 1
        max_no_improve = 500  # Small instances
    elif 143 <= dimension <= 916:
        theta = 2
        max_no_improve = 250  # Medium instances
    elif dimension == 1001:
        theta = 3
        max_no_improve = 100  # Large instances
    else:
        raise ValueError("Instance dimension out of expected range.")

    # Compute execution time in whole minutes
    exe_time_minutes = round((theta * dimension / 100) * 60)

    return exe_time_minutes, max_no_improve


def solve_with_aco(cevrp: CEVRP, selected_file_instance:str, start_time_seconds) -> tuple:
    """Solves the instance using ACO and returns the computed paths and cost."""

    # Step 1: Build the graph
    manager = CoordinatesManager(cevrp.node_coord_section)
    manager.compute_distances()
    graph = manager.build_graph()

    exe_time_minutes, max_no_improve = compute_execution_params(selected_file_instance)
    stop_time = start_time + (exe_time_minutes * 60)  # Convert minutes to seconds
    # Step 2: Initialize ACO
    aco = ACO(graph,max_ant_steps=config.max_ant_steps,
        num_iterations=config.num_iterations, best_path_cost=cevrp.optimal_value,
        cevrp=cevrp, max_iteration_improvement=max_no_improve, exec_time=stop_time,
    )

    # Step 3: Solve the ACO routing problem
    flatten_paths, initial_cost, paths = aco.find_shortest_path(
        start=config.default_source_node,
        num_ants=config.num_ants,
    )

    # Raise an exception if no valid solution is found
    if not flatten_paths and initial_cost == float('inf') and not paths:
        raise NoSolutionFoundError("ACO did not find a valid solution.")

    # Step 4: Visualize the routes BEFORE optimization
    aco.graph_api.visualize_graph(paths, cevrp.charging_stations, f"Initial Routes - {cevrp.name}")

    # Step 5: Apply 2-opt Optimization
    paths_2opt = [apply_2opt(path, aco.graph_api) for path in paths]

    # Step 6: Visualize the routes AFTER 2-opt
    aco.graph_api.visualize_graph(paths_2opt, cevrp.charging_stations, f"After 2-opt - {cevrp.name}")

    # Step 7: Apply 2-opt-star Optimization
    paths_2opt_star = apply_2opt_star(paths_2opt, aco.graph_api, cevrp)

    # Step 8: Visualize the routes AFTER 2-opt-star
    aco.graph_api.visualize_graph(paths_2opt_star, cevrp.charging_stations, f"After 2-opt-star - {cevrp.name}")

    # Step 9: Apply node-shift Optimization
    paths_node_shift = apply_node_shift(paths_2opt_star, aco.graph_api, cevrp)

    # Step 10: Visualize the routes AFTER 2-opt
    aco.graph_api.visualize_graph(paths_node_shift, cevrp.charging_stations, f"After node-shift - {cevrp.name}")

    # Step 11: Compute optimized cost only if paths changed
    optimized_cost = aco.graph_api.calculate_paths_cost(paths_node_shift) if paths_node_shift != paths else initial_cost

    return (flatten_paths, optimized_cost, paths_node_shift), aco.graph_api


def solve_with_alns(paths: List[Path], cevrp: CEVRP) -> tuple:
    """Applies ALNS to improve the routes found by ACO."""
    cevrp.add_charging_stations_to_nodes()
    manager = CoordinatesManager(cevrp.node_coord_section)
    manager.compute_distances()
    graph = manager.build_graph()
    graph_api = GraphApi(graph)

    cevrp_state = CevrpState(paths, graph_api=graph_api, cevrp=cevrp, visualization=config.alns_visualization)
    return make_alns(
        cevrp_state,
        destroy_operators=[remove_charging_station, worst_removal, cluster_removal],
        repair_operators=[greedy_insertion, regret_k_insertion, best_feasible_insertion],
        num_iterations= config.alns_iterations,
    ), graph_api


if __name__ == '__main__':
    try:
        selected_file = select_instance(config.instance_files)
        print(f"Selected instance: {selected_file}")

        cevrp_instance = create_cevrp_instance(selected_file)


        # Solve using ACO
        start_time = time.time()
        (aco_flatten_paths, aco_cost, aco_paths), aco_graph_api = solve_with_aco(
            cevrp_instance, selected_file, start_time)

        execution_time = time.time() - start_time
        print(f"⏱ ACO Solution Execution time: {int(execution_time // 60)}m {execution_time % 60:.2f}s")
        print(f"ACO - Initial routes:\n{format_path(aco_paths)}")
        print(f"ACO - Initial total cost: {aco_cost}")
        aco_graph_api.visualize_graph(aco_paths, cevrp_instance.charging_stations, cevrp_instance.name)

        # Apply ALNS
        start_time = time.time()
        (best_state, best_cost, best_paths, unassigned_nodes), alns_graph_api = solve_with_alns(aco_paths,                                                                              cevrp_instance)
        execution_time = time.time() - start_time
        print(f"⏱ ALNS Optimization Execution time: {int(execution_time // 60)}m {execution_time % 60:.2f}s")
        print(f"ALNS - Final routes:\n{format_path(best_paths)}")
        print(f"ALNS - Final total cost: {best_cost}")

        alns_graph_api.visualize_graph(best_paths, cevrp_instance.charging_stations, cevrp_instance.name)

    except NoSolutionFoundError as e:
        print(e)

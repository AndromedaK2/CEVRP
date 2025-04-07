import os
import sys
import time
from typing import List

from ALNS_METAHEURISTIC.destroy_operators import remove_charging_station, worst_removal, cluster_removal
from ALNS_METAHEURISTIC.make_alns import make_alns
from ALNS_METAHEURISTIC.repair_operators import greedy_insertion, regret_k_insertion, best_feasible_insertion
from ALNS_METAHEURISTIC.solution_state import CevrpState
from Shared.Utils.helper import format_path, create_cevrp_instance, select_instance, compute_execution_params
from Shared.experiment import Experiment, config
from Shared.Utils.exceptions import NoSolutionFoundError
from Shared.graph_api import GraphApi
from Shared.heuristic import apply_2opt, apply_2opt_star, apply_node_shift
from Shared.path import Path
from Shared.Utils.coordinates_manager import CoordinatesManager
from MMAS.aco import ACO
from Shared.cevrp import CEVRP




def solve_with_aco(cevrp: CEVRP, selected_file_instance:str, experiment_aco:Experiment, start_time_aco: float) -> tuple:
    """Solves the instance using ACO and returns the computed paths and cost."""

    # Step 1: Build the graph
    manager = CoordinatesManager(cevrp.node_coord_section)
    manager.compute_distances()
    graph = manager.build_graph()

    exe_time_minutes, max_no_improve = compute_execution_params(selected_file_instance)
    stop_time = start_time_aco + (exe_time_minutes * 60)  # Convert minutes to seconds
    # Step 2: Initialize ACO
    aco = ACO(graph, max_ant_steps=experiment_aco.max_ant_steps,
              num_iterations=experiment_aco.num_iterations, best_path_cost=cevrp.optimal_value,
              cevrp=cevrp, max_iteration_improvement=max_no_improve, exec_time=stop_time,
              )

    # Step 3: Solve the ACO routing problem
    flatten_paths, initial_cost, paths = aco.find_shortest_path(
        start=config.default_source_node,
        num_ants=experiment_aco.num_ants,
    )

    # Raise an exception if no valid solution is found
    if not flatten_paths and initial_cost == float('inf') and not paths:
        raise NoSolutionFoundError("ACO did not find a valid solution.")


    # Step 4: Visualize the routes BEFORE optimization
    aco.graph_api.visualize_graph(paths, cevrp.charging_stations, f"Initial Routes - {cevrp.name}", experiment_aco.directory_path)

    # Step 5: Apply 2-opt Optimization
    paths_2opt = [apply_2opt(path, aco.graph_api) for path in paths]

    # Step 6: Visualize the routes AFTER 2-opt
    aco.graph_api.visualize_graph(paths_2opt, cevrp.charging_stations, f"After 2-opt - {cevrp.name}",experiment_aco.directory_path)

    # Step 7: Apply 2-opt-star Optimization
    paths_2opt_star = apply_2opt_star(paths_2opt, aco.graph_api, cevrp)

    # Step 8: Visualize the routes AFTER 2-opt-star
    aco.graph_api.visualize_graph(paths_2opt_star, cevrp.charging_stations, f"After 2-opt-star - {cevrp.name}",experiment_aco.directory_path)

    # Step 9: Apply node-shift Optimization
    paths_node_shift = apply_node_shift(paths_2opt_star, aco.graph_api, cevrp)

    # Step 10: Visualize the routes AFTER 2-opt
    aco.graph_api.visualize_graph(paths_node_shift, cevrp.charging_stations, f"After node-shift - {cevrp.name}",experiment_aco.directory_path)

    # Step 11: Compute optimized cost only if paths changed
    optimized_cost = aco.graph_api.calculate_paths_cost(paths_node_shift) if paths_node_shift != paths else initial_cost

    return (flatten_paths, optimized_cost, paths_node_shift), aco.graph_api


def solve_with_alns(paths: List[Path], cevrp: CEVRP, experiment_alns:Experiment) -> tuple:
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
        num_iterations= experiment_alns.alns_iterations,
        rw_decay=experiment_alns.rw_decay,
        rw_weights=experiment_alns.rw_weights,
        autofit_end_threshold=experiment_alns.autofit_end_threshold,
        autofit_start_threshold=experiment_alns.autofit_start_threshold,
        directory_path=experiment_alns.directory_path
    ), graph_api


if __name__ == '__main__':
    try:
        if len(sys.argv) > 1:
            instance_index = int(sys.argv[1]) - 1  # User provides 1-based index, adjust to 0-based
            if instance_index < 0 or instance_index >= len(config.instance_files):
                raise ValueError("❌ Invalid instance index passed via command-line.")
            selected_file = config.instance_files[instance_index]
        else:
            selected_file = select_instance(config.instance_files)

        cevrp_instance = create_cevrp_instance(selected_file)
        experiment = Experiment.create_experiment_config(cevrp_instance,selected_file)
        log_filename = os.path.join(experiment.directory_path, "execution_log.txt")

        def log(message):
            print(message)
            with open(log_filename, "a", encoding="utf-8") as log_file:
                log_file.write("\n" + message + "\n")


        log(f"Selected instance: {selected_file}")

        # Solve using ACO
        start_time = time.time()
        (aco_flatten_paths, aco_cost, aco_paths), aco_graph_api = solve_with_aco(
            cevrp_instance, selected_file, experiment, start_time)

        execution_time = time.time() - start_time
        log(f"⏱ ACO Solution Execution time: {int(execution_time // 60)}m {execution_time % 60:.2f}s")
        log(f"ACO - Initial routes:\n{format_path(aco_paths)}")
        log(f"ACO - Initial total cost: {aco_cost}")

        # Apply ALNS
        start_time = time.time()
        (best_state, best_cost, best_paths, unassigned_nodes), alns_graph_api = solve_with_alns(aco_paths,
                                                                                                cevrp_instance,
                                                                                                experiment)

        execution_time = time.time() - start_time
        log(f"⏱ ALNS Optimization Execution time: {int(execution_time // 60)}m {execution_time % 60:.2f}s")
        log(f"ALNS - Final routes:\n{format_path(best_paths)}")
        log(f"ALNS - Final total cost: {best_cost}")
        log(f"================================================================================================")

        alns_graph_api.visualize_graph(best_paths, cevrp_instance.charging_stations, cevrp_instance.name, experiment.directory_path)


    except NoSolutionFoundError as e:
        print(e)

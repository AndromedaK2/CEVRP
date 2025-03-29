from alns import ALNS
import numpy.random as rnd
from alns.accept import RecordToRecordTravel
from alns.select import RouletteWheel
from alns.stop import MaxIterations
from matplotlib import pyplot as plt, colors
import uuid
from ALNS_METAHEURISTIC.destroy_operators import remove_overcapacity_nodes
from ALNS_METAHEURISTIC.repair_functions import insert_charging_stations_after_each_node
from ALNS_METAHEURISTIC.repair_operators import smart_reinsertion
from ALNS_METAHEURISTIC.solution_state import CevrpState
from Shared.heuristic import apply_local_search

SEED = 1234

def make_alns(
    initial_state: CevrpState,
    num_iterations: int = 20,
    destroy_operators: list = None,
    repair_operators: list = None,
    rw_weights: list = None,
    rw_decay: float = 0.8,
    autofit_start_threshold: float = 0.02,
    autofit_end_threshold: float = 0,
    directory_path: str = ""
) -> tuple :
    """
    Configures and runs the ALNS algorithm for the CEVRP problem.

    :param directory_path: Directory path to save experiments
    :param initial_state: Initial solution state for the CEVRP problem.
    :param num_iterations: Maximum number of iterations for the algorithm.
    :param destroy_operators: List of destroy operators to use.
    :param repair_operators: List of repair operators to use.
    :param rw_weights: Initial weights for the RouletteWheel selection mechanism.
    :param rw_decay: Decay rate for the RouletteWheel weights.
    :param autofit_start_threshold: Starting threshold for RecordToRecordTravel.
    :param autofit_end_threshold: Ending threshold for RecordToRecordTravel.
    :return: The result of the ALNS algorithm.
    """
    # Initialize ALNS with a seeded random number generator
    alns = ALNS(rnd.default_rng(SEED))

    initial_state =  insert_charging_stations_after_each_node(initial_state)

    # Add destroy operators (default to random_destroy if none provided)
    if destroy_operators is None:
        destroy_operators = [remove_overcapacity_nodes]
    for operator in destroy_operators:
        alns.add_destroy_operator(operator)

    # Add repair operators (default to greedy_repair if none provided)
    if repair_operators is None:
        repair_operators = [smart_reinsertion]
    for operator in repair_operators:
        alns.add_repair_operator(operator)

    # Configure the selection mechanism (RouletteWheel)
    if rw_weights is None:
        rw_weights = [25, 5, 1, 0.5]
    select = RouletteWheel(
        scores=rw_weights,
        decay=rw_decay,
        num_destroy=len(destroy_operators),
        num_repair=len(repair_operators),
    )

    # Configure the acceptance criterion (RecordToRecordTravel)
    accept = RecordToRecordTravel.autofit(
        initial_state.objective(), autofit_start_threshold, autofit_end_threshold, num_iterations
    )

    # Configure the stopping criterion (MaxIterations)
    stop = MaxIterations(num_iterations)

    # Apply Random Local Search
    alns.on_best(apply_local_search)


    # Run the ALNS algorithm
    result = alns.iterate(initial_state, select, accept, stop)

    # Plot the objective value progression
    fig, ax = plt.subplots(figsize=(20, 10))
    result.plot_objectives(ax=ax)

    plt.subplots_adjust(left=0.2)
    ax.yaxis.set_tick_params(labelsize=14)

    plt.title("Objective Value Progress", fontsize=16)

    plt.savefig(f"./{directory_path}/operator_count-{result.best_state.objective()}.png")

    fig, ax = plt.subplots(figsize=(12, 12))

    result.plot_operator_counts(
        fig=fig,
    )
    ax.set_xticks([])
    plt.subplots_adjust(
        left=0.2,
        right=0.95,
        top=0.95,
        bottom=0.1
    )


    plt.savefig(f"./{directory_path}/objective_value_progress-{result.best_state.objective()}.png")

    # Extract the best solution state
    best_state = result.best_state


    # Extract the total cost of the best solution
    best_cost = best_state.objective()

    # Extract the list of paths in the best solution
    best_paths = best_state.paths

    # Extract the list of unassigned nodes in the best solution
    unassigned_nodes = best_state.unassigned

    # Return the final solution details
    return best_state, best_cost, best_paths, unassigned_nodes

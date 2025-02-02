from alns import ALNS, Result
import numpy.random as rnd
from alns.accept import RecordToRecordTravel
from alns.select import RouletteWheel
from alns.stop import MaxIterations

from ALNS_METAHEURISTIC.destroy_operators import random_destroy
from ALNS_METAHEURISTIC.repair_operators import greedy_repair
from ALNS_METAHEURISTIC.solution_state import CevrpState

SEED = 1234

def make_alns(
    initial_state: CevrpState,
    num_iterations: int = 1000,
    destroy_operators: list = None,
    repair_operators: list = None,
    rw_weights: list = None,
    rw_decay: float = 0.8,
    autofit_start_threshold: float = 0.02,
    autofit_end_threshold: float = 0
) :
    """
    Configures and runs the ALNS algorithm for the CEVRP problem.

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

    # Add destroy operators (default to random_destroy if none provided)
    if destroy_operators is None:
        destroy_operators = [random_destroy]
    for operator in destroy_operators:
        alns.add_destroy_operator(operator)

    # Add repair operators (default to greedy_repair if none provided)
    if repair_operators is None:
        repair_operators = [greedy_repair]
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

    # Run the ALNS algorithm
    result = alns.iterate(initial_state, select, accept, stop)

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

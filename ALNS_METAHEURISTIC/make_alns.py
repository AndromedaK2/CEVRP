
from alns import ALNS
import numpy.random as rnd
from alns.accept import RecordToRecordTravel
from alns.select import RouletteWheel
from alns.stop import MaxIterations

from ALNS_METAHEURISTIC.destroy_operators import random_destroy
from ALNS_METAHEURISTIC.repair_operators import greedy_repair
from ALNS_METAHEURISTIC.solution_state import CevrpState

SEED = 1234

def make_alns(cevrpState:CevrpState) -> ALNS:
    alns = ALNS(rnd.default_rng(SEED))

    alns.add_destroy_operator(random_destroy)

    alns.add_repair_operator(greedy_repair)

    num_iterations = 3000
    select = RouletteWheel([25, 5, 1, 0], 0.8, 1, 1)
    accept = RecordToRecordTravel.autofit(
        cevrpState.objective(), 0.02, 0, num_iterations
    )
    stop = MaxIterations(num_iterations)

    result = alns.iterate(cevrpState, select, accept, stop)

    return result

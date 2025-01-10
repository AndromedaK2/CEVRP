
from alns import ALNS
import numpy as np
import numpy.random as rnd

from ALNS_METAHEURISTIC.destroy_operators import random_destroy
from Shared.path import Path

SEED = 1234

def make_alns() -> ALNS:
    alns = ALNS(rnd.default_rng(SEED))

    alns.add_destroy_operator(random_destroy)

    #alns.add_repair_operator(random_repair)

    return alns

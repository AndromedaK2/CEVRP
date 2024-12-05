import math
import random
from typing import Dict


def compute_edge_desirability(
        pheromone_value: float, edge_cost: float, alpha: float, beta: float
) -> float:
    return pow(pheromone_value, alpha) * pow((1 / edge_cost), beta)


def roulette_wheel_selection(probabilities: Dict[str, float]) -> str:
    """source: https://en.wikipedia.org/wiki/Fitness_proportionate_selection"""
    sorted_probabilities = {
        k: v for k, v in sorted(probabilities.items(), key=lambda item: -item[1])
    }

    """ probabilities = {"A": 0.3, "B": 0.5, "C": 0.2}
        ordered       = {"B": 0.5, "A": 0.3, "C": 0.2}
    """
    pick = random.random()
    current = 0.0
    for node, fitness in sorted_probabilities.items():
        current += fitness
        if current > pick:
            return node
    raise Exception("Edge case for roulette wheel selection")


def boundaries_pheromones_levels_validate(pheromone_value: float, max_pheromone_level: float,
                                          min_pheromone_level: float) -> float:
    """Returns pheromones levels within a certain range."""
    return min(max(pheromone_value, min_pheromone_level), max_pheromone_level)


def calculate_phi_max(rho: float, xgb: float) -> float:
    """
    Calculates φmax based on the given formula.

    Args:
        rho (float): Evaporation coefficient (0 < rho < 1).
        xgb (float): Global best solution (distance cost).

    Returns:
        float: Calculated value of φmax.
    """
    if rho <= 0 or rho >= 1:
        raise ValueError("The value of rho must be in the range (0, 1).")

    # Calculate φmax
    phi_max = 1 / ((1 - rho) * xgb)

    # Return φmax and xgb (global best solution)
    return phi_max


def calculate_phi_min(phi_max: float, n: int, pr: float = 0.05) -> float:
    """
    Calculates φmin using the n-th root of pr.

    Args:
        phi_max (float): Calculated value of φmax.
        n (int): Index of the root (n-th root).
        pr (float): Probability or related parameter.

    Returns:
        float: Calculated value of φmin.
    """
    if n <= 2:
        raise ValueError("The value of n must be greater than 2.")
    if pr <= 0 or pr > 1:
        raise ValueError("The value of pr must be in the range (0, 1].")

    # Calculate the n-th root of pr
    nth_root_pr = math.pow(pr, 1 / n)

    # Calculate numerator and denominator
    numerator = 1 - (1 / nth_root_pr)
    denominator = (n / 2) - 1

    # Calculate φmin
    phi_min = phi_max * (numerator / denominator) * (1 / nth_root_pr)

    return phi_min


def calculate_pheromone_value(evaporation_rate: float, pheromone_value: float, path_cost: float, total_customers: int):
    new_pheromone_value = (evaporation_rate * pheromone_value) + (1 / path_cost)
    max_pheromone_level = calculate_phi_max(evaporation_rate, path_cost)
    min_pheromone_level = calculate_phi_min(max_pheromone_level, total_customers)
    return boundaries_pheromones_levels_validate(new_pheromone_value, max_pheromone_level, min_pheromone_level)

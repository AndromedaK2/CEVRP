import math
import random
from typing import Dict


def compute_edge_desirability(
        pheromone_value: float, edge_cost: float, alpha: float, beta: float
) -> float:
    if edge_cost == 0.0:
        return 0
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


def calculate_phi_max(evaporation_rate: float, best_path_cost: float) -> float:
    """
    Calculates φmax based on the given formula.

    Args:
        evaporation_rate (float): Evaporation coefficient (0 < rho < 1).
        best_path_cost (float): Global best solution (distance cost).

    Returns:
        float: Calculated value of φmax.
    """
    if evaporation_rate <= 0 or evaporation_rate >= 1:
        raise ValueError("The value of rho must be in the range (0, 1).")

    # Calculate φmax
    max_pheromone_level = 1 / ((1 - evaporation_rate) * best_path_cost)

    # Return φmax and xgb (global best solution)
    return max_pheromone_level


def calculate_phi_min(max_pheromone_level: float, total_customers: int, pr: float = 0.05) -> float:
    """
    Calculates φmin using the n-th root of pr.

    Args:
        max_pheromone_level (float): Calculated value of φmax.
        total_customers (int): Index of the root (n-th root).
        pr (float): Probability or related parameter.

    Returns:
        float: Calculated value of φmin.
    """
    if total_customers <= 2:
        raise ValueError("The value of n must be greater than 2.")
    if pr <= 0 or pr > 1:
        raise ValueError("The value of pr must be in the range (0, 1].")

    # Calculate the n-th root of pr
    nth_root_pr = math.pow(pr, 1 / total_customers)

    # Calculate numerator and denominator
    numerator = 1 - (1 / nth_root_pr)
    denominator = (total_customers / 2) - 1

    # Calculate φmin
    min_pheromone_level = max_pheromone_level * (numerator / denominator) * (1 / nth_root_pr)

    return min_pheromone_level


def calculate_pheromone_value(evaporation_rate: float, pheromone_value: float, best_path_cost: float, total_customers: int):
    new_pheromone_value = (evaporation_rate * pheromone_value) + (1 / best_path_cost)
    max_pheromone_level = calculate_phi_max(evaporation_rate, best_path_cost)
    min_pheromone_level = calculate_phi_min(max_pheromone_level, total_customers)
    return boundaries_pheromones_levels_validate(new_pheromone_value, max_pheromone_level, min_pheromone_level)

import math
import random
from typing import Dict





def compute_edge_desirability(
        pheromone_value: float, edge_cost: float, alpha: float, beta: float
) -> float:
    """
    Compute desirability of an edge based on pheromone value and edge cost.

    Args:
        pheromone_value (float): The level of pheromone on the edge.
        edge_cost (float): The cost of traversing the edge.
        alpha (float): Pheromone influence exponent.
        beta (float): Edge cost influence exponent.
        φ^α_ij / d^β_ij

    Returns:
        float: Calculated desirability of the edge.
    """
    if edge_cost == 0.0:
        return 0
    return pow(pheromone_value, alpha) * pow(1 / edge_cost, beta)


def roulette_wheel_selection(probabilities: Dict[str, float], seed: int = 1234) -> str:
    """
    Selects an element based on probability in a roulette wheel fashion.
    source: https://en.wikipedia.org/wiki/Fitness_proportionate_selection

    Args:
        probabilities (Dict[str, float]): A dictionary with elements as keys and probabilities as values.

    Returns:
        str: Selected element based on probability distribution.
        :param probabilities:
        :param seed:
    """
    random.seed(seed)
    sorted_probabilities = dict(sorted(probabilities.items(), key=lambda item: -item[1]))
    pick = random.random()
    current = 0.0
    for node, fitness in sorted_probabilities.items():
        current += fitness
        if current > pick:
            return node
    raise RuntimeError("Edge case for roulette wheel selection")


def validate_pheromone_levels(pheromone_value: float, max_level: float, min_level: float) -> float:
    """
    Returns pheromone levels within a certain range.

    Args:
        pheromone_value (float): Current pheromone value.
        max_level (float): Maximum allowed pheromone level.
        min_level (float): Minimum allowed pheromone level.

    Returns:
        float: Adjusted pheromone value within the specified range.
    """
    return min(max(pheromone_value, min_level), max_level)


def calculate_max_phi(evaporation_rate: float, best_path_cost: float) -> float:
    """
    Calculates φmax based on the given formula.

    Args:
        evaporation_rate (float): Evaporation coefficient (0 < rho < 1).
        best_path_cost (float): Global best solution (distance cost).

    Returns:
        float: Calculated value of φmax.
    """
    if not 0 < evaporation_rate < 1:
        raise ValueError("The value of rho must be in the range (0, 1).")
    return 1 / ((1 - evaporation_rate) * best_path_cost)


def calculate_min_phi(max_level: float, total_customers: int, pr: float = 0.05) -> float:
    """
    Calculates φmin using the n-th root of pr.

    Args:
        max_level (float): Calculated value of φmax.
        total_customers (int): Index of the root (n-th root).
        pr (float): Probability or related parameter.

    Returns:
        float: Calculated value of φmin.
    """
    if total_customers <= 2:
        raise ValueError("The value of n must be greater than 2.")
    if not 0 < pr <= 1:
        raise ValueError("The value of pr must be in the range (0, 1].")
    nth_root_pr = math.pow(pr, 1 / total_customers)
    numerator = 1 - (1 / nth_root_pr)
    denominator = (total_customers / 2) - 1
    return max_level * (numerator / denominator) * (1 / nth_root_pr)


def calculate_pheromone_value(evaporation_rate: float, pheromone_value: float, best_path_cost: float,
                              total_customers: int) -> float:
    """
    Calculate the new pheromone value for an edge.

    Args:
        evaporation_rate (float): The rate at which pheromone evaporates.
        pheromone_value (float): Current pheromone value.
        best_path_cost (float): Cost of the best path found.
        total_customers (int): Number of customers/nodes involved.

    Returns:
        float: New adjusted pheromone value.
    """
    new_value = (evaporation_rate * pheromone_value) + (1 / best_path_cost)
    max_level = calculate_max_phi(evaporation_rate, best_path_cost)
    min_level = calculate_min_phi(max_level, total_customers)
    return validate_pheromone_levels(new_value, max_level, min_level)

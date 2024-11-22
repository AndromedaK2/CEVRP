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

def boundaries_pheromones_levels_validate(pheromone_value: float, max_pheromone_level: float, min_pheromone_level: float) -> float:
    """Returns pheromones levels within a certain range."""
    return max(min_pheromone_level, min(pheromone_value, max_pheromone_level))

def calculate_phi_max(rho: float, f: float, xgb: float) -> float:
    """
    Calcula φmax según la fórmula dada.

    Args:
        rho (float): Coeficiente de evaporación (0 < rho < 1).
        f (float): Parámetro asociado a la función objetivo.
        xgb (float): Solución global mejor (costo de la distancia).

    Returns:
        float: Valor calculado de φmax.
    """
    if rho <= 0 or rho >= 1:
        raise ValueError("El valor de rho debe estar en el rango (0, 1).")

    # Calcular φmax
    phi_max = 1 / ((1 - rho) * f)

    # Retornar φmax y xgb (solución global mejor)
    return phi_max, xgb
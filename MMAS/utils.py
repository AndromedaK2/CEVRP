import random
from typing import Dict

import networkx as nx


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


def create_graph_from_manager(manager):
    G = nx.DiGraph()

    # Añadir todos los nodos
    for _, row in manager.cities.iterrows():
        G.add_node(row['ID'], pos=(row['X'], row['Y']), demand=row['Demand'])

    # Añadir todas las aristas
    distances = manager.get_distances()
    for i in distances.index:
        for j in distances.columns:
            if i != j:
                G.add_edge(i, j, cost=distances.loc[i, j])

    return G

def show_graph(G):
    # Imprimir algunas estadísticas del grafo
    print(f"Número de nodos: {G.number_of_nodes()}")
    print(f"Número de aristas: {G.number_of_edges()}")

    # Imprimir algunas aristas como ejemplo
    print("\nAlgunas aristas del grafo:")
    for i, (u, v, data) in enumerate(G.edges(data=True)):
            print(f"Arista de {u} a {v} con costo {data['cost']:.2f}")

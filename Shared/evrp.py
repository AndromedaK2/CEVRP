import numpy as np
from typing import List, Dict


class EVRP:
    def __init__(self,
                 name: str,
                 comment: str,
                 instance_type: str,
                 optimal_value: float,
                 vehicles: int,
                 dimension: int,
                 stations: int,
                 capacity: int,
                 energy_capacity: int,
                 energy_consumption: float,
                 edge_weight_format: str,
                 node_coord_section: np.ndarray,
                 demand_section: Dict[int, int],
                 stations_coord_section: List[int],
                 depot_section: List[int]):
        self.name = name
        self.comment = comment
        self.instance_type = instance_type
        self.optimal_value = optimal_value
        self.vehicles = vehicles
        self.dimension = dimension
        self.stations = stations
        self.capacity = capacity
        self.energy_capacity = energy_capacity
        self.energy_consumption = energy_consumption
        self.edge_weight_format = edge_weight_format
        self.node_coord_section = node_coord_section
        self.demand_section = demand_section
        self.stations_coord_section = stations_coord_section
        self.depot_section = depot_section

    @staticmethod
    def parse_evrp_instance_from_file(file_path: str) -> "EVRP":
        with open(file_path, 'r') as file:
            lines = file.readlines()

        instance_data = {}
        node_coord_list = []
        demand_dict = {}
        stations_coord_section = []
        depot_section = []

        section = None
        for line in lines:
            line = line.strip()
            if "NODE_COORD_SECTION" in line:
                section = "NODE_COORD_SECTION"
            elif "DEMAND_SECTION" in line:
                section = "DEMAND_SECTION"
            elif "STATIONS_COORD_SECTION" in line:
                section = "STATIONS_COORD_SECTION"
            elif "DEPOT_SECTION" in line:
                section = "DEPOT_SECTION"
            elif "EOF" in line:
                break
            elif section == "NODE_COORD_SECTION":
                node_coord_list.append(list(map(int, line.split())))
            elif section == "DEMAND_SECTION":
                node, demand = map(int, line.split())
                demand_dict[node] = demand
            elif section == "STATIONS_COORD_SECTION":
                stations_coord_section.append(int(line.strip()))
            elif section == "DEPOT_SECTION":
                depot_section.append(int(line.strip()))
            elif line:  # Líneas de metadatos (fuera de las secciones)
                key, value = line.split(": ", 1)
                instance_data[key.strip()] = value.strip()

        # Crear arreglo numpy con coordenadas y demandas
        node_coord_array = []
        for coord in node_coord_list:
            node_id = coord[0]
            demand = demand_dict.get(node_id, 0)  # Si no hay demanda, se asigna 0
            node_coord_array.append(coord + [demand])  # Agregar demanda como último valor

        node_coord_section = np.array(node_coord_array)

        return EVRP(
            name=instance_data["Name"],
            comment=instance_data["COMMENT"],
            instance_type=instance_data["TYPE"],
            optimal_value=float(instance_data["OPTIMAL_VALUE"]),
            vehicles=int(instance_data["VEHICLES"]),
            dimension=int(instance_data["DIMENSION"]),
            stations=int(instance_data["STATIONS"]),
            capacity=int(instance_data["CAPACITY"]),
            energy_capacity=int(instance_data["ENERGY_CAPACITY"]),
            energy_consumption=float(instance_data["ENERGY_CONSUMPTION"]),
            edge_weight_format=instance_data["EDGE_WEIGHT_FORMAT"],
            node_coord_section=node_coord_section,
            demand_section=demand_dict,
            stations_coord_section=stations_coord_section,
            depot_section=depot_section
        )

    @staticmethod
    def drain_battery(current_battery: float, distance_cost: int, energy_consumption: float) -> float:
        """
        Reduce la batería restante en función del costo de distancia y el consumo de energía.
        """
        new_current_battery = current_battery - (distance_cost * energy_consumption)
        return max(0.0, new_current_battery)  # Evitar batería negativa

    @property
    def charge_battery(self) -> float:
        """
        Retorna la capacidad máxima de la batería para esta instancia.
        """
        return self.energy_capacity

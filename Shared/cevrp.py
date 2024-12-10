from dataclasses import dataclass, field

import numpy as np
from typing import List, Dict


@dataclass
class CEVRP:
    name: str = "Default Name"
    comment: str = "Default Comment"
    instance_type: str = "Default Type"
    optimal_value: float = 0.0
    vehicles: int = 1
    dimension: int = 1
    stations: int = 0
    capacity: int = 1000
    energy_capacity: int = 100
    energy_consumption: float = 1.0
    edge_weight_format: str = "Default Format"
    node_coord_section: np.ndarray = field(default_factory=lambda: np.array([]))
    demand_section: Dict[int, int] = field(default_factory=dict)
    stations_coord_section: List[int] = field(default_factory=list)
    depot_section: List[int] = field(default_factory=list)

    @staticmethod
    def parse_evrp_instance_from_file(file_path: str, include_stations: bool = False) -> "CEVRP":
        """
                Reads an EVRP instance from a file and parses it into an EVRP object.
                :param file_path: Path to the text file containing the EVRP instance.
                :param include_stations: Indicates whether to include charging stations (zero demands).
                :return: EVRP instance.
        """
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
            elif line:
                key, value = line.split(": ", 1)
                instance_data[key.strip()] = value.strip()
        node_coord_array = []
        # Check if stations should be included
        if include_stations:
            # Process all nodes, including stations
            for coord in node_coord_list:
                node_id = coord[0]  # The first value in coord is the node ID
                demand = demand_dict.get(node_id, 0)
                # If the node is a station, subtract the station coordinates
                if node_id in stations_coord_section:
                    station_coord = stations_coord_section[node_id]  # Ensure this is the correct format
                    coord = [c - station_coord for c in coord]  # Subtract the station's coordinates
                node_coord_array.append(coord + [demand])
        # If stations are not included, only process nodes with demand > 0
        else:
            for coord in node_coord_list:
                node_id = coord[0]  # The first value in coord is the node ID
                demand = demand_dict.get(node_id, 0)
                # Include node 1 (depot) or nodes with demand > 0
                if node_id == 1 or demand > 0:
                    node_coord_array.append(coord + [demand])
        node_coord_section = np.array(node_coord_array)
        # Use the file name (without the path) as the name property
        file_name = file_path.split("/")[-1].split("\\")[-1]  # Handles both / and \ paths
        return CEVRP(
            name=file_name,  # Set the name to the file name
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
        Reduces the remaining battery based on the distance cost and energy consumption.
        """

        new_current_battery = current_battery - (distance_cost * energy_consumption)
        return max(0.0, new_current_battery)

    @property
    def charge_battery(self) -> float:
        """
        Returns the maximum battery capacity for this instance.
        """
        return self.energy_capacity

from dataclasses import dataclass, field
from typing import List, Dict
import numpy as np
import pandas as pd


@dataclass
class CEVRP:
    """
    Represents an Electric Vehicle Routing Problem (EVRP) instance.
    """
    name: str = "Default Name"
    comment: str = "Default Comment"
    instance_type: str = "Default Type"
    optimal_value: float = 0.0
    vehicles: int = 1
    dimension: int = 1
    stations: int = 0
    capacity: int = 1000
    energy_capacity: float = 100
    energy_consumption: float = 1.0
    edge_weight_format: str = "Default Format"
    node_coord_section: np.ndarray = field(default_factory=lambda: np.array([]))
    demand_section: Dict[int, int] = field(default_factory=dict)
    stations_coord_section: np.ndarray = field(default_factory=lambda: np.array([]))
    charging_stations: List[str] = field(default_factory=list)
    depot_section: List[int] = field(default_factory=list)

    @staticmethod
    def parse_evrp_instance_from_file(file_path: str, include_stations: bool = False) -> "CEVRP":
        """
        Reads an EVRP instance from a file and parses it into a CEVRP object.

        :param file_path: Path to the text file containing the EVRP instance.
        :param include_stations: Whether to include charging stations (zero demands).
        :return: A CEVRP instance.
        """
        with open(file_path, 'r') as file:
            lines = file.readlines()

        instance_data = {}
        node_coord_list = []
        demand_dict = {}
        charging_stations = []
        depot_section = []
        section = None

        for line in lines:
            line = line.strip()
            if not line or "EOF" in line:
                continue

            # Identify the current section
            if "SECTION" in line:
                section = line
                continue

            # Process data based on the current section
            if section == "NODE_COORD_SECTION":
                node_coord_list.append(list(map(int, line.split())))
            elif section == "DEMAND_SECTION":
                node, demand = map(int, line.split())
                demand_dict[node] = demand
            elif section == "STATIONS_COORD_SECTION":
                charging_stations.append(str(line.strip()))
            elif section == "DEPOT_SECTION":
                depot_section.append(int(line.strip()))
            else:
                # Parse key-value pairs for instance metadata
                key, value = line.split(": ", 1)
                instance_data[key.strip()] = value.strip()

        station_coord_array = [[*coord, 0] for coord in node_coord_list if str(coord[0]) in charging_stations]

        if include_stations:
            node_coord_array = [[*coord, demand_dict.get(coord[0], 0)] for coord in node_coord_list]
        else:
            node_coord_array = [[*coord, demand_dict.get(coord[0], 0)] for coord in node_coord_list if
                                str(coord[0]) not in charging_stations]

        # Convert lists to numpy arrays
        node_coord_section = np.array(node_coord_array)
        stations_coord_section = np.array(station_coord_array)

        # Extract file name for the instance name
        file_name = file_path.split("/")[-1].split("\\")[-1]



        return CEVRP(
            name=file_name,
            comment=instance_data.get("COMMENT", "Default Comment"),
            instance_type=instance_data.get("TYPE", "Default Type"),
            optimal_value=float(instance_data.get("OPTIMAL_VALUE", 0.0)),
            vehicles=int(instance_data.get("VEHICLES", 1)),
            dimension=int(instance_data.get("DIMENSION", 1)),
            stations=int(instance_data.get("STATIONS", 0)),
            capacity=int(instance_data.get("CAPACITY", 1000)),
            energy_capacity=int(instance_data.get("ENERGY_CAPACITY", 100)),
            energy_consumption=float(instance_data.get("ENERGY_CONSUMPTION", 1.0)),
            edge_weight_format=instance_data.get("EDGE_WEIGHT_FORMAT", "Default Format"),
            node_coord_section=node_coord_section,
            demand_section=demand_dict,
            stations_coord_section=stations_coord_section,
            charging_stations=charging_stations,
            depot_section=depot_section,
        )


    def add_charging_stations_to_nodes(self):
        """
        Adds charging station coordinates to node_coord_section if not already included.
        """
        if self.stations_coord_section.size == 0:
            return
        self.node_coord_section = np.vstack((self.node_coord_section, self.stations_coord_section))

    @staticmethod
    def get_benchmark() -> pd.DataFrame:
        """
        Returns a DataFrame containing benchmark data for EVRP instances.
        """
        data = {
            "name": [
                "E-n22-k4.evrp", "E-n23-k3.evrp", "E-n30-k3.evrp", "E-n33-k4.evrp",
                "E-n51-k5.evrp", "E-n76-k7.evrp", "E-n101-k8.evrp", "X-n143-k7.evrp",
                "X-n214-k11.evrp", "X-n352-k40.evrp", "X-n459-k26.evrp", "X-n573-k30.evrp",
                "X-n685-k75.evrp", "X-n749-k98.evrp", "X-n819-k171.evrp", "X-n916-k207.evrp",
                "X-n1001-k43.evrp"
            ],
            "#customers": [21, 22, 29, 32, 50, 75, 100, 142, 213, 351, 458, 572, 684, 748, 818, 915, 1000],
            "#depots": [1] * 17,
            "#stations": [8, 9, 6, 6, 5, 7, 9, 4, 9, 35, 20, 6, 25, 30, 25, 9, 9],
            "#routes": [4, 3, 4, 4, 5, 7, 8, 7, 11, 40, 26, 30, 75, 98, 171, 207, 43],
            "C": [6000, 4500, 4500, 8000, 160, 220, 200, 1190, 944, 436, 1106, 210, 408, 396, 358, 33, 131],
            "Q": [94, 190, 178, 209, 105, 98, 103, 2243, 987, 649, 929, 1691, 911, 790, 926, 1591, 1684],
            "h": [1.2] * 7 + [1.0] * 10,
            "UB": [384.67, 573.13, 511.25, 869.89, 570.17, 723.36, 899.88, "–", "–", "–", "–", "–", "–", "–", "–", "–", "–"]
        }

        return pd.DataFrame(data)
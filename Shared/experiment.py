import os
from datetime import datetime
from typing import List
from dataclasses import dataclass

from Shared.cevrp import CEVRP

#Const
INSTANCE_FILES: List[str] = [
    "Shared/Instances/E-n22-k4.evrp",
    "Shared/Instances/E-n23-k3.evrp",
    "Shared/Instances/E-n30-k3.evrp",
    "Shared/Instances/E-n33-k4.evrp",
    "Shared/Instances/E-n51-k5.evrp",
    "Shared/Instances/E-n76-k7.evrp",
    "Shared/Instances/E-n101-k8.evrp",
    "Shared/Instances/X-n143-k7.evrp",
    "Shared/Instances/X-n214-k11.evrp",
    "Shared/Instances/X-n351-k40.evrp",
    "Shared/Instances/X-n459-k26.evrp",
    "Shared/Instances/X-n573-k30.evrp",
    "Shared/Instances/X-n685-k75.evrp",
    "Shared/Instances/X-n749-k98.evrp",
    "Shared/Instances/X-n819-k171.evrp",
    "Shared/Instances/X-n916-k207.evrp",
    "Shared/Instances/X-n1001-k43.evrp"
]
CUSTOMERS: List[int] = [
    23,
    24,
    31,
    34,
    52,
    76,
    102,
    144,
    215,
    352,
    460,
    574,
    686,
    750,
    820,
    917,
    1002
]



# Without use
NUM_ITERATIONS: int = 50
MAX_ITERATION_IMPROVEMENT: int = 5
ALNS_ITERATIONS: int = 200
CUSTOMER_LIKE_ANT: bool = True

# Dont Touch
MAX_ANT_STEPS: int = 10000
DEFAULT_SOURCE_NODE: str = "1"

# Variable
ACO_VISUALIZATION: bool = False
ALNS_VISUALIZATION: bool = False
EXPERIMENT_TYPE = "baseline"


@dataclass
class Experiment:
    num_ants: int
    max_ant_steps: int
    num_iterations: int
    max_iteration_improvement: int
    alns_iterations: int
    rw_weights: List[int]
    rw_decay: float
    autofit_start_threshold: float
    autofit_end_threshold: float
    directory_path:str



    @staticmethod
    def create_experiment_config(cevrp_instance:CEVRP, selected_file:str) -> "Experiment":


        def get_num_ants(cevrp:CEVRP):
            num_ants = len(cevrp.node_coord_section) + 1
            return num_ants


        selected_file_path = selected_file.replace("Shared/Instances/", "").replace(".evrp", "")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        directory_path = f"experiments/{EXPERIMENT_TYPE}/{selected_file_path}/{timestamp}"
        if not os.path.exists(directory_path):
            os.makedirs(directory_path, exist_ok=True)

        if EXPERIMENT_TYPE == "baseline":
            return Experiment(
                # CONSTANTS
                max_ant_steps=MAX_ANT_STEPS,
                max_iteration_improvement=MAX_ITERATION_IMPROVEMENT,
                # VARIABLES
                num_ants= get_num_ants(cevrp_instance),
                num_iterations=30,
                rw_weights=[25, 5, 1, 0.5],
                rw_decay=0.8,
                autofit_start_threshold=0.02,
                autofit_end_threshold=0,
                alns_iterations=30,
                directory_path=directory_path
            )
        elif EXPERIMENT_TYPE == "optimized":
            return Experiment(
                # CONSTANTS
                max_ant_steps=MAX_ANT_STEPS,
                max_iteration_improvement=MAX_ITERATION_IMPROVEMENT,
                # VARIABLES
                num_ants= get_num_ants(cevrp_instance) if CUSTOMER_LIKE_ANT else 10 ,
                num_iterations=10,
                rw_weights=[8, 5, 1, 0.5],
                rw_decay=0.8,
                autofit_start_threshold=0.02,
                autofit_end_threshold=0,
                alns_iterations=50,
                directory_path=directory_path
            )
        elif EXPERIMENT_TYPE == "custom":
            return Experiment(
                # CONSTANTS
                max_ant_steps=MAX_ANT_STEPS,
                max_iteration_improvement=MAX_ITERATION_IMPROVEMENT,
                # VARIABLES
                num_iterations=50,
                num_ants= get_num_ants(cevrp_instance) if CUSTOMER_LIKE_ANT else 500 ,
                rw_weights=[25, 5, 1, 0.5],
                rw_decay=0.8,
                autofit_start_threshold=0.02,
                autofit_end_threshold=0,
                alns_iterations=ALNS_ITERATIONS,
                directory_path=directory_path
            )
        return Experiment(
            num_ants=get_num_ants(cevrp_instance),
            max_ant_steps=MAX_ANT_STEPS,
            # VARIABLES
            num_iterations=50,
            rw_weights=[25, 5, 1, 0.5],
            rw_decay=0.8,
            autofit_start_threshold=0.02,
            autofit_end_threshold=0,
            max_iteration_improvement=MAX_ITERATION_IMPROVEMENT,
            alns_iterations=ALNS_ITERATIONS,
            directory_path=directory_path
        )


@dataclass
class Config:
    instance_files: List[str]
    default_source_node: str
    customers: List[int]
    aco_visualization: bool
    alns_visualization: bool

config = Config(
    instance_files=INSTANCE_FILES,
    default_source_node=DEFAULT_SOURCE_NODE,
    customers=CUSTOMERS,
    aco_visualization=ACO_VISUALIZATION,
    alns_visualization=ALNS_VISUALIZATION)

from typing import List
from dataclasses import dataclass


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


NUM_ANTS: int = 30
MAX_ANT_STEPS: int = 10000

DEFAULT_SOURCE_NODE: str = "1"
NUM_ITERATIONS: int = 50
ACO_VISUALIZATION: bool = False
MAX_ITERATION_IMPROVEMENT: int = 5

ALNS_ITERATIONS: int = 200
ALNS_VISUALIZATION: bool = False

EXPERIMENT_TYPE = "baseline"


@dataclass
class Config:
    instance_files: List[str]
    default_source_node: str
    num_ants: int
    max_ant_steps: int
    num_iterations: int
    max_iteration_improvement: int
    aco_visualization: bool
    alns_iterations: int
    alns_visualization: bool

    @staticmethod
    def create_experiment_config() -> "Config":
        if EXPERIMENT_TYPE == "baseline":
            return Config(
                # CONSTANTS
                instance_files=INSTANCE_FILES,
                default_source_node=DEFAULT_SOURCE_NODE,
                num_ants=NUM_ANTS,
                max_ant_steps=MAX_ANT_STEPS,
                # VARIABLES
                num_iterations=NUM_ITERATIONS,
                max_iteration_improvement=MAX_ITERATION_IMPROVEMENT,
                aco_visualization=ACO_VISUALIZATION,
                alns_iterations=ALNS_ITERATIONS,
                alns_visualization=ALNS_VISUALIZATION,
            )
        elif EXPERIMENT_TYPE == "optimized":
            return Config(
                # CONSTANTS
                instance_files=INSTANCE_FILES,
                default_source_node=DEFAULT_SOURCE_NODE,
                num_ants=NUM_ANTS,
                max_ant_steps=MAX_ANT_STEPS,
                # VARIABLES
                num_iterations=NUM_ITERATIONS,
                max_iteration_improvement=MAX_ITERATION_IMPROVEMENT,
                aco_visualization=ACO_VISUALIZATION,
                alns_iterations=ALNS_ITERATIONS,
                alns_visualization=ALNS_VISUALIZATION,
            )
        elif EXPERIMENT_TYPE == "custom":
            return Config(
                # CONSTANTS
                instance_files=INSTANCE_FILES,
                default_source_node=DEFAULT_SOURCE_NODE,
                num_ants=NUM_ANTS,
                max_ant_steps=MAX_ANT_STEPS,
                # VARIABLES
                num_iterations=NUM_ITERATIONS,
                max_iteration_improvement=MAX_ITERATION_IMPROVEMENT,
                aco_visualization=ACO_VISUALIZATION,
                alns_iterations=ALNS_ITERATIONS,
                alns_visualization=ALNS_VISUALIZATION,
            )
        return Config(
            # CONSTANTS
            instance_files=INSTANCE_FILES,
            default_source_node=DEFAULT_SOURCE_NODE,
            num_ants=NUM_ANTS,
            max_ant_steps=MAX_ANT_STEPS,
            # VARIABLES
            num_iterations=NUM_ITERATIONS,
            max_iteration_improvement=MAX_ITERATION_IMPROVEMENT,
            aco_visualization=ACO_VISUALIZATION,
            alns_iterations=ALNS_ITERATIONS,
            alns_visualization=ALNS_VISUALIZATION,
        )


config = Config(
    instance_files=INSTANCE_FILES,
    default_source_node=DEFAULT_SOURCE_NODE,
    num_ants=NUM_ANTS,
    max_ant_steps=MAX_ANT_STEPS,
    num_iterations=NUM_ITERATIONS,
    alns_iterations=ALNS_ITERATIONS,
    alns_visualization=ALNS_VISUALIZATION,
    aco_visualization=ACO_VISUALIZATION,
    max_iteration_improvement=MAX_ITERATION_IMPROVEMENT,
)

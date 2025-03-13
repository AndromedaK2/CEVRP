from typing import List

from Shared.cevrp import CEVRP
from Shared.path import Path


def select_instance(instance_files: List[str]) -> str:
    """Prompts the user to select an instance file from a list."""
    print("Select an instance by entering its number:")
    for idx, file_path in enumerate(instance_files):
        print(f"{idx + 1}: {file_path}")
    while True:
        try:
            selection = int(input("Enter the number of the instance: ")) - 1
            if 0 <= selection < len(instance_files):
                return instance_files[selection]
            print("Invalid selection. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def create_cevrp_instance(file_path: str) -> CEVRP:
    """Parses and creates a CEVRP instance from the selected file path."""
    try:
        cevrp = CEVRP.parse_evrp_instance_from_file(file_path, include_stations=False)
        print(f"✅ Instance successfully created from: {file_path}")
        return cevrp
    except FileNotFoundError:
        raise FileNotFoundError(f"❌ File {file_path} not found.")
    except Exception as exception:
        raise RuntimeError(f"❌ Error creating instance from {file_path}: {exception}")


def format_path(paths: List[Path]) -> str:
    """Formats and returns a string representation of routes."""
    header = ("\n".join([
        "╔════════════════════════════════════════╗",
        "║               Found Routes             ║",
        "╚════════════════════════════════════════╝"
    ]))

    formatted_routes = [header]
    for idx, path in enumerate(paths, start=1):
        route_str = " -> ".join(path.nodes)
        formatted_routes.append(f"► Route {idx}: {route_str}\n  Cost: {path.path_cost}")
        formatted_routes.append("-----------------------------------------")

    return "\n".join(formatted_routes)


def compute_execution_params(instance_name: str) -> tuple:
    """
    Compute the execution time (ExeTime) in minutes, along with max_no_improve,
    based on the instance name and number of nodes.

    Parameters:
        instance_name (str): Name of the instance, e.g., 'Shared/Instances/E-n22-k4.evrp'.

    Returns:
        tuple: (exe_time_minutes, max_no_improve)
    """
    # Extract the instance identifier (e.g., 'E-n22-k4')
    instance_id = instance_name.split('/')[-1].replace('.evrp', '')

    # Extract numerical part from instance name
    dimension = int(instance_id.split('-')[1][1:])

    # Determine problem category and theta value
    if 22 <= dimension <= 101:
        max_no_improve = 1000
        theta = 1
    elif 143 <= dimension <= 916:
        theta = 2
        max_no_improve = 100  # Small instances
    elif dimension == 1001:
        max_no_improve = 100  # Small instances
        theta = 3
    else:
        raise ValueError("Instance dimension out of expected range.")

    # Compute execution time in whole minutes
    exe_time_minutes = round((theta * dimension / 100) * 60)

    return exe_time_minutes, max_no_improve
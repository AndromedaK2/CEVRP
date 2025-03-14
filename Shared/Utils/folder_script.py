import os

# Locate the project root dynamically
project_root = os.path.dirname(os.path.abspath(__file__))  # Current script's directory

# Ensure we're at the root (CEVRP), not inside Shared/Utils/experiments/
while not os.path.exists(os.path.join(project_root, "main.py")):
    project_root = os.path.dirname(project_root)  # Move up one level

# Define the experiments directory inside the root of the project
experiments_dir = os.path.join(project_root, "Experiments")

# List of instances with file paths
INSTANCE_FILES = [
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

# Extract folder names by removing path and extension
instance_names = [os.path.splitext(os.path.basename(path))[0] for path in INSTANCE_FILES]

# Main subdirectories inside "experiments"
main_folders = ["baseline", "optimized", "custom"]

# Create folders inside "experiments"
for main_folder in main_folders:
    folder_root = os.path.join(experiments_dir, main_folder)  # Ensure all are inside "experiments"
    for instance_name in instance_names:
        folder_path = os.path.join(folder_root, instance_name)
        os.makedirs(folder_path, exist_ok=True)
        print(f"Created: {folder_path}")

print("✅ All folders have been created successfully inside 'CEVRP/experiments/'.")

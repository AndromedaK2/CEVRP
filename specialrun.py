import subprocess
import os

# Path to the Python executable in the virtual environment
python_executable = r"C:\Users\Tesis\Desktop\CEVRP\.venv\Scripts\python.exe"

# Path to the main script that needs to be executed
main_script_path = r"C:\Users\Tesis\PycharmProjects\CEVRP\main.py"

def run_parallel():
    # Get user input for the instance and the number of parallel runs
    param = input("Select instance 1 to 17: ").strip()
    try:
        n = int(input("How many parallel runs of main.py do you want? "))
    except ValueError:
        print("❌ Invalid input. Please enter a valid number.")
        return

    processes = []

    # Launch parallel runs
    for i in range(n):
        print(f"🚀 Launching parallel run #{i + 1} with param {param}")
        command = [python_executable, main_script_path, param]
        try:
            process = subprocess.Popen(command)
            processes.append(process)
        except FileNotFoundError as e:
            print(f"❌ Error in launching process: {e}")

    print("\n⏳ Waiting for all runs to finish...\n")

    # Wait for each process to complete
    for i, p in enumerate(processes, 1):
        p.wait()
        if p.returncode == 0:
            print(f"✅ Run #{i} completed successfully")
        else:
            print(f"❌ Run #{i} failed with return code {p.returncode}")

if __name__ == "__main__":
    run_parallel()

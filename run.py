import subprocess
import os

python_executable = os.path.join(os.getcwd(), '.venv', 'Scripts', 'python.exe')

def run_main_in_parallel():
    try:
        instance_number = input("Select instance (1 to 17): ").strip()
        n = int(input("How many parallel runs of main.py do you want? "))
    except ValueError:
        print("❌ Invalid input. Please enter valid numbers.")
        return

    processes = []

    for i in range(n):
        run_id = str(i + 1)
        print(f"🚀 Launching Run #{run_id} for Instance {instance_number}")
        process = subprocess.Popen([
            python_executable, "main.py", instance_number, run_id
        ])
        processes.append(process)

    print("\n⏳ Waiting for all runs to finish...\n")

    for i, p in enumerate(processes, 1):
        p.wait()
        if p.returncode == 0:
            print(f"✅ Run #{i} completed successfully")
        else:
            print(f"❌ Run #{i} failed with return code {p.returncode}")

if __name__ == "__main__":
    run_main_in_parallel()

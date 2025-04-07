import subprocess
import os

python_executable = os.path.join(os.getcwd(), '.venv', 'Scripts', 'python.exe')

def run_main_in_parallel():
    try:
        param = input("Select instance 1 to 17: ").strip()
        n = int(input("How many parallel runs of main.py do you want? "))
    except ValueError:
        print("❌ Invalid input. Please enter valid numbers.")
        return

    processes = []

    for i in range(n):
        print(f"🚀 Launching parallel run #{i + 1} with param {param}")
        process = subprocess.Popen([python_executable, "main.py", param])
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

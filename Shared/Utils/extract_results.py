import os
import re
import pandas as pd

# Rutas base del proyecto
project_root = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(project_root, "main.py")):
    project_root = os.path.dirname(project_root)

experiments_dir = os.path.join(project_root, "Experiments")
results_dir = os.path.join(project_root, "Results")

def extract_data_from_log(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()

    # Separar bloques ACO y ALNS
    aco_blocks = re.split(r'(?=⏱ ACO Solution Execution time:)', content)
    alns_blocks = re.split(r'(?=⏱ ALNS Optimization Execution time:)', content)

    # Limpiar encabezados vacíos si los hay
    aco_blocks = [b for b in aco_blocks if "ACO Solution Execution time" in b]
    alns_blocks = [b for b in alns_blocks if "ALNS Optimization Execution time" in b]

    # Unir por índice (asume que están en orden)
    num_executions = min(len(aco_blocks), len(alns_blocks))
    extracted_runs = []

    for i in range(num_executions):
        aco_block = aco_blocks[i]
        alns_block = alns_blocks[i]

        run_data = {}

        # ACO
        match_aco_time = re.search(r'⏱ ACO Solution Execution time: (\d+m \d+\.\d+s)', aco_block)
        match_aco_cost = re.search(r'ACO - Initial total cost:\s*([\d,\.]+)', aco_block)
        run_data["ACO_time"] = match_aco_time.group(1) if match_aco_time else None
        if match_aco_cost:
            val = match_aco_cost.group(1).replace(',', '')
            run_data["ACO_initial_cost"] = float(val) if re.match(r'^\d+\.?\d*$', val) else None
        else:
            run_data["ACO_initial_cost"] = None

        # ALNS
        match_alns_time = re.search(r'⏱ ALNS Optimization Execution time: (\d+m \d+\.\d+s)', alns_block)
        match_alns_cost = re.search(r'ALNS - Final total cost:\s*([\d,\.]+)', alns_block)
        run_data["ALNS_time"] = match_alns_time.group(1) if match_alns_time else None
        if match_alns_cost:
            val = match_alns_cost.group(1).replace(',', '')
            run_data["ALNS_final_cost"] = float(val) if re.match(r'^\d+\.?\d*$', val) else None
        else:
            run_data["ALNS_final_cost"] = None

        extracted_runs.append(run_data)

    return extracted_runs


def process_experiment(experiment_type, output_format="csv"):
    results = []
    experiment_path = os.path.join(experiments_dir, experiment_type)

    if not os.path.exists(experiment_path):
        print(f"La carpeta del experimento '{experiment_type}' no existe.")
        return

    output_dir = os.path.join(results_dir, experiment_type)
    os.makedirs(output_dir, exist_ok=True)

    for instance in os.listdir(experiment_path):
        instance_path = os.path.join(experiment_path, instance)
        if not os.path.isdir(instance_path):
            continue

        ejecucion_id = 1

        # Caso 1: execution_log.txt directamente en la instancia
        log_file_in_root = os.path.join(instance_path, 'execution_log.txt')
        if os.path.exists(log_file_in_root):
            runs = extract_data_from_log(log_file_in_root)
            for run in runs:
                results.append({
                    'Experimento': experiment_type,
                    'Instancia': instance,
                    'Ejecucion': ejecucion_id,
                    **run
                })
                ejecucion_id += 1

        # Caso 2: subdirectorios con logs
        subdirs = sorted([d for d in os.listdir(instance_path)
                          if os.path.isdir(os.path.join(instance_path, d))])
        for subdir in subdirs:
            subdir_path = os.path.join(instance_path, subdir)
            log_file = os.path.join(subdir_path, 'execution_log.txt')
            if os.path.exists(log_file):
                runs = extract_data_from_log(log_file)
                for run in runs:
                    results.append({
                        'Experimento': experiment_type,
                        'Instancia': instance,
                        'Ejecucion': ejecucion_id,
                        **run
                    })
                    ejecucion_id += 1
            else:
                print(f"Archivo log no encontrado: {log_file}")

    df = pd.DataFrame(results)

    if output_format == "csv":
        output_file = os.path.join(output_dir, f'resultados_{experiment_type}.csv')
        df.to_csv(output_file, index=False)
    elif output_format == "excel":
        output_file = os.path.join(output_dir, f'resultados_{experiment_type}.xlsx')
        df.to_excel(output_file, index=False)
    else:
        print(f"Formato de salida '{output_format}' no soportado.")
        return

    print(f'Resultados guardados en {output_file}')



if __name__ == "__main__":
    experiment_options = {
        "1": "baseline",
        "2": "optimized",
        "3": "custom",
        "4": "refactored"
    }

    format_options = {
        "1": "csv",
        "2": "excel"
    }

    print("Selecciona el tipo de experimento:")
    for key, name in experiment_options.items():
        print(f"{key}: {name}")
    experiment_choice = input("Opción: ").strip()
    experiment_type = experiment_options.get(experiment_choice)

    print("\nSelecciona el formato de salida:")
    for key, name in format_options.items():
        print(f"{key}: {name}")
    format_choice = input("Opción: ").strip()
    output_format = format_options.get(format_choice)

    if experiment_type and output_format:
        process_experiment(experiment_type, output_format)
    else:
        print("Opción inválida. Asegúrate de elegir un número válido.")
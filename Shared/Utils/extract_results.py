import os
import re
import pandas as pd


project_root = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(project_root, "main.py")):
    project_root = os.path.dirname(project_root)

experiments_dir = os.path.join(project_root, "Experiments")
results_dir = os.path.join(project_root, "Results")


patterns = {
    'ACO_time': r'⏱ ACO Solution Execution time: (\d+m \d+\.\d+s)',
    'ACO_initial_cost': r'ACO - Initial total cost:\s*([\d,\.]+)',
    'ALNS_time': r'⏱ ALNS Optimization Execution time: (\d+m \d+\.\d+s)',
    'ALNS_final_cost': r'ALNS - Final total cost:\s*([\d,\.]+)'
}


def extract_data_from_log(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()

    extracted_data = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        value = match.group(1).strip() if match else None

        if key in ['ACO_initial_cost', 'ALNS_final_cost'] and value:
            value = value.replace(',', '')
            value = re.sub(r'[^\d\.]', '', value)
            if not re.match(r'^\d+\.?\d*$', value):
                value = None

        extracted_data[key] = value
    return extracted_data


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
        if os.path.isdir(instance_path):
            for execution_num, execution in enumerate(sorted(os.listdir(instance_path)), 1):
                execution_path = os.path.join(instance_path, execution)
                log_file = os.path.join(execution_path, 'execution_log.txt')
                if os.path.exists(log_file):
                    data = extract_data_from_log(log_file)
                    results.append({
                        'Experimento': experiment_type,
                        'Instancia': instance,
                        'Ejecucion': execution_num,
                        **data
                    })
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
from nicegui import ui
import subprocess
import re

# Define regex patterns to extract the required information
pattern = re.compile(r'Testing machine_capacity=(\d+), processing_time=\((\d+\.\d+), (\d+\.\d+)\), interval=\((\d+\.\d+), (\d+\.\d+)\)\nResults: Average Waiting Time=(\d+\.\d+) minutes, Machine Utilization=(\d+\.\d+)%')
best_config_pattern = re.compile(r'Best Configuration: machine_capacity=(\d+), num_parts=(\d+), inter_arrival_time=\((\d+\.\d+), (\d+\.\d+)\), processing_time=\((\d+\.\d+), (\d+\.\d+)\)\nBest Results: Average Waiting Time=(\d+\.\d+) minutes, Machine Utilization=(\d+\.\d+)%')

def run_simulation(random_seed, num_parts, machine_capacities, processing_times, initial_inter_arrival_range):
    result = subprocess.run(
        ['python', 'simulation_program.py', random_seed, num_parts, machine_capacities, processing_times, initial_inter_arrival_range],
        capture_output=True,
        text=True
    )

    content = result.stdout
    best_configuration = None
    best_results = None
    all_results = []

    matches = pattern.findall(content)
    for match in matches:
        all_results.append({
            'machine_capacity': match[0],
            'processing_time': f"({match[1]}, {match[2]})",
            'interval': f"({match[3]}, {match[4]})",
            'num_parts': num_parts,
            'inter_arrival_time': initial_inter_arrival_range,
            'average_waiting_time': match[5],
            'machine_utilization': match[6]
        })

    best_match = best_config_pattern.search(content)
    if best_match:
        best_configuration = {
            'machine_capacity': best_match[1],
            'num_parts': best_match[2],
            'inter_arrival_time': f"({best_match[3]}, {best_match[4]})",
            'processing_time': f"({best_match[5]}, {best_match[6]})"
        }
        best_results = {
            'average_waiting_time': best_match[7],
            'machine_utilization': best_match[8]
        }

    return all_results, best_configuration, best_results

def main():
    with ui.card().classes('p-4'):
        ui.label('Enter Simulation Parameters').classes('text-h5')
        random_seed = ui.input('Random Seed (e.g., 42)').classes('mb-2')
        num_parts = ui.input('Number of Parts (e.g., 200)').classes('mb-2')
        machine_capacities = ui.input('Machine Capacities (e.g., 4, 6, 8)').classes('mb-2')
        processing_times = ui.input('Processing Times (e.g., 4-6,5-7)').classes('mb-2')
        initial_inter_arrival_range = ui.input('Initial Inter-Arrival Time Range (e.g., 1.0-10.0)').classes('mb-2')
        run_button = ui.button('Run Simulation').classes('mb-2')

        results_section = ui.column().classes('hidden')
        best_configuration_table = ui.table().classes('mb-4')
        all_results_table = ui.table()

        def on_run_button_click():
            results_section.classes(remove='hidden')
            all_results, best_configuration, best_results = run_simulation(
                random_seed.value, num_parts.value, machine_capacities.value, processing_times.value, initial_inter_arrival_range.value
            )

            best_configuration_table.rows = [
                ['Machine Capacity', 'Num Parts', 'Inter-Arrival Time', 'Processing Time', 'Average Waiting Time (minutes)', 'Machine Utilization (%)']
            ]
            if best_configuration and best_results:
                best_configuration_table.rows.append([
                    best_configuration['machine_capacity'],
                    best_configuration['num_parts'],
                    best_configuration['inter_arrival_time'],
                    best_configuration['processing_time'],
                    best_results['average_waiting_time'],
                    best_results['machine_utilization']
                ])
            else:
                best_configuration_table.rows.append(['No configuration met the criteria.'])

            all_results_table.rows = [
                ['Machine Capacity', 'Processing Time', 'Interval', 'Num Parts', 'Inter-Arrival Time', 'Average Waiting Time (minutes)', 'Machine Utilization (%)']
            ]
            for result in all_results:
                all_results_table.rows.append([
                    result['machine_capacity'],
                    result['processing_time'],
                    result['interval'],
                    result['num_parts'],
                    result['inter_arrival_time'],
                    result['average_waiting_time'],
                    result['machine_utilization']
                ])

        run_button.on('click', on_run_button_click)

    ui.run()

if __name__ == '__main__':
    main()
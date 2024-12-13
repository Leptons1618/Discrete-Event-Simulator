from nicegui import ui
import subprocess
import re
import threading
import logging
import signal
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)

# Define regex patterns to extract the required information
pattern = re.compile(r'Testing machine_capacity=(\d+), processing_time=\((\d+\.\d+), (\d+\.\d+)\), interval=\((\d+\.\d+), (\d+\.\d+)\)\nResults: Average Waiting Time=(\d+\.\d+) minutes, Machine Utilization=(\d+\.\d+)%')
best_config_pattern = re.compile(r'Best Configuration: machine_capacity=(\d+), num_parts=(\d+), inter_arrival_time=\((\d+\.\d+), (\d+\.\d+)\), processing_time=\((\d+\.\d+), (\d+\.\d+)\)\nBest Results: Average Waiting Time=(\d+\.\d+) minutes, Machine Utilization=(\d+\.\d+)%')

def run_simulation(random_seed, num_parts, machine_capacities, processing_times, initial_inter_arrival_range):
    logging.info('Starting simulation with parameters: %s, %s, %s, %s, %s',
                 random_seed, num_parts, machine_capacities, processing_times, initial_inter_arrival_range)
    
    # Convert all parameters to strings
    args = [
        'python', 'simulation_program.py',
        str(random_seed),
        str(num_parts),
        machine_capacities,
        processing_times,
        initial_inter_arrival_range
    ]
    
    result = subprocess.run(args, capture_output=True, text=True)
    
    # Check for errors
    if result.returncode != 0:
        logging.error('Simulation program exited with errors:\n%s', result.stderr)
        return [], None, None

    content = result.stdout
    best_configuration = None
    best_results = None
    all_results = []

    # Updated regex patterns to match integers and decimals
    number_pattern = r'([0-9]+(?:\.[0-9]+)?)'
    pattern = re.compile(
        r'Testing machine_capacity=(\d+), processing_time=\(' + number_pattern + r', ' + number_pattern + r'\), '
        r'interval=\(' + number_pattern + r', ' + number_pattern + r'\)\n'
        r'Results: Average Waiting Time=' + number_pattern + r' minutes, Machine Utilization=' + number_pattern + r'%'
    )
    best_config_pattern = re.compile(
        r'Best Configuration: machine_capacity=(\d+), num_parts=(\d+), inter_arrival_time=\(' + number_pattern + r', ' + number_pattern + r'\), '
        r'processing_time=\(' + number_pattern + r', ' + number_pattern + r'\)\n'
        r'Best Results: Average Waiting Time=' + number_pattern + r' minutes, Machine Utilization=' + number_pattern + r'%'
    )

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

    logging.info('Simulation completed')
    logging.info(best_results)
    return all_results, best_configuration, best_results

def main():
    simulation_thread = None

    def on_run_button_click():
        nonlocal simulation_thread

        def run_simulation_thread():
            results_section.classes(remove='hidden')
            all_results, best_configuration, best_results = run_simulation(
                random_seed.value, num_parts.value, machine_capacities.value, processing_times.value, initial_inter_arrival_range.value
            )
            
            if best_configuration and best_results:
                best_configuration_data = [{'machine_capacity': best_configuration['machine_capacity'],
                                            'num_parts': best_configuration['num_parts'],
                                            'inter_arrival_time': best_configuration['inter_arrival_time'],
                                            'processing_time': best_configuration['processing_time'],
                                            'average_waiting_time': best_results['average_waiting_time'],
                                            'machine_utilization': best_results['machine_utilization']}]
                best_configuration_table.rows = best_configuration_data
            else:
                best_configuration_table.rows.append(['No configuration met the criteria.'])
            
            all_results_table.rows = all_results

        if simulation_thread and simulation_thread.is_alive():
            logging.warning('Simulation is already running')
        else:
            simulation_thread = threading.Thread(target=run_simulation_thread)
            simulation_thread.start()

    def signal_handler(sig, frame):
        logging.info('Exiting program')
        if simulation_thread and simulation_thread.is_alive():
            simulation_thread.join()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    with ui.row().classes('h-screen').style('flex-wrap: nowrap;'):
        with ui.column().classes('w-1/4 p-4 bg-gray-100 border-r'):
            ui.label('Parameters').classes('text-h6 mb-4')
            random_seed = ui.input('Random Seed (e.g., 42)').classes('mb-4')
            num_parts = ui.input('Number of Parts (e.g., 200)').classes('mb-4')
            machine_capacities = ui.input('Machine Capacities (e.g., 4,6,8)').classes('mb-4')
            processing_times = ui.input('Processing Times (e.g., 4-6,5-7)').classes('mb-4')
            initial_inter_arrival_range = ui.input('Inter-Arrival Time Range (e.g., 1.0-10.0)').classes('mb-4')
            run_button = ui.button('Run').classes('mt-auto')

        with ui.column().classes('w-3/4 p-4'):
            results_section = ui.column()
            with results_section:
                ui.label('Best Configuration').classes('text-h6 mb-2')
                best_configuration_table = ui.table(columns=[
                    {'name': 'machine_capacity', 'label': 'Machine Capacity', 'field': 'machine_capacity', 'required': True, 'align': 'left'},
                    {'name': 'num_parts', 'label': 'Num Parts', 'field': 'num_parts', 'sortable': True},
                    {'name': 'inter_arrival_time', 'label': 'Inter-Arrival Time', 'field': 'inter_arrival_time', 'sortable': True},
                    {'name': 'processing_time', 'label': 'Processing Time', 'field': 'processing_time', 'sortable': True},
                    {'name': 'average_waiting_time', 'label': 'Average Waiting Time (minutes)', 'field': 'average_waiting_time', 'sortable': True},
                    {'name': 'machine_utilization', 'label': 'Machine Utilization (%)', 'field': 'machine_utilization', 'sortable': True},
                ], rows=[], row_key='machine_capacity').classes('mb-4')
                ui.label('All Results').classes('text-h6 mb-2')
                all_results_table = ui.table(columns=[
                    {'name': 'machine_capacity', 'label': 'Machine Capacity', 'field': 'machine_capacity', 'required': True, 'align': 'left'},
                    {'name': 'processing_time', 'label': 'Processing Time', 'field': 'processing_time', 'sortable': True},
                    {'name': 'interval', 'label': 'Interval', 'field': 'interval', 'sortable': True},
                    {'name': 'num_parts', 'label': 'Num Parts', 'field': 'num_parts', 'sortable': True},
                    {'name': 'inter_arrival_time', 'label': 'Inter-Arrival Time', 'field': 'inter_arrival_time', 'sortable': True},
                    {'name': 'average_waiting_time', 'label': 'Average Waiting Time (minutes)', 'field': 'average_waiting_time', 'sortable': True},
                    {'name': 'machine_utilization', 'label': 'Machine Utilization (%)', 'field': 'machine_utilization', 'sortable': True},
                ], rows=[], row_key='machine_capacity')

        run_button.on('click', on_run_button_click)

    ui.run(native=True, window_size=(1600, 980))

if __name__ in {"__main__", "__mp_main__"}:
    main()
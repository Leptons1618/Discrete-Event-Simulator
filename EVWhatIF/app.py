from nicegui import ui
import subprocess
import re
import threading
import logging
import signal
import sys
from datetime import datetime

# Configure logging
log_filename = './logs/application.log'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[ 
    logging.FileHandler(log_filename),
    logging.StreamHandler()
])

# Define regex patterns to extract the required information
pattern = re.compile(r'Average waiting time: (\d+\.\d+) minutes\nCharging point utilization: (\d+\.\d+)%')

def run_simulation(num_charging_points, num_vehicles, charging_time, operating_hours):
    logging.info('Starting simulation with parameters: %s, %s, %s, %s',
                 num_charging_points, num_vehicles, charging_time, operating_hours)
    
    # Convert all parameters to strings
    args = [
        'python', 'evWhatif.py',
        str(num_charging_points),
        str(num_vehicles),
        str(charging_time[0]), str(charging_time[1]),
        str(operating_hours)
    ]
    
    result = subprocess.run(args, capture_output=True, text=True)
    
    # Check for errors
    if result.returncode != 0:
        logging.error('Simulation program exited with errors:\n%s', result.stderr)
        return None, None

    content = result.stdout
    match = pattern.search(content)
    if match:
        avg_waiting_time = float(match.group(1))
        utilization = float(match.group(2))
        return avg_waiting_time, utilization
    else:
        return None, None

def main():
    simulation_thread = None

    def on_run_button_click():
        nonlocal simulation_thread

        def run_simulation_thread():
            results_section.classes(remove='hidden')
            avg_waiting_time, utilization = run_simulation(
                num_charging_points.value, num_vehicles.value, (charging_time_min.value, charging_time_max.value), operating_hours.value
            )
            
            if avg_waiting_time is not None and utilization is not None:
                results_table.rows = [{
                    'avg_waiting_time': avg_waiting_time,
                    'utilization': utilization
                }]
                logging.info(f"Simulation Results: Average Waiting Time: {avg_waiting_time:.2f} minutes, Charging Point Utilization: {utilization:.2f}%")
            else:
                results_table.rows.append(['Simulation failed.'])
                logging.error('Simulation failed.')

            logging.info('-' * 60)

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
        # Parameters section
        with ui.column().classes('w-1/4 p-4 bg-gray-100 border-r').style('background-color: #f8f9fa; border-right: 1px solid #dee2e6;'):
            ui.label('Parameters').classes('text-h6 mb-4').style('font-weight: bold; color: #343a40;')
            num_charging_points = ui.input(label='Number of Charging Points', placeholder='e.g., 5', autocomplete=['4', '5', '6']).classes('mb-4').style('border: 1px solid #ced4da; border-radius: 0.25rem; padding: 0.375rem 0.75rem;')
            num_vehicles = ui.input(label='Number of Vehicles', placeholder='e.g., 50', autocomplete=['50', '60', '70']).classes('mb-4').style('border: 1px solid #ced4da; border-radius: 0.25rem; padding: 0.375rem 0.75rem;')
            charging_time_min = ui.input(label='Charging Time Min (minutes)', placeholder='e.g., 30', autocomplete=['20', '30', '40']).classes('mb-4').style('border: 1px solid #ced4da; border-radius: 0.25rem; padding: 0.375rem 0.75rem;')
            charging_time_max = ui.input(label='Charging Time Max (minutes)', placeholder='e.g., 60', autocomplete=['40', '50', '60']).classes('mb-4').style('border: 1px solid #ced4da; border-radius: 0.25rem; padding: 0.375rem 0.75rem;')
            operating_hours = ui.input(label='Operating Hours', placeholder='e.g., 12', autocomplete=['12', '14', '16']).classes('mb-4').style('border: 1px solid #ced4da; border-radius: 0.25rem; padding: 0.375rem 0.75rem;')
            run_button = ui.button('Run').classes('mt-auto')

        # Results section
        with ui.column().classes('w-3/4 p-4'):
            results_section = ui.column()
            with results_section:
                ui.label('Simulation Results').classes('text-h6 mb-2')
                results_table = ui.table(columns=[
                    {'name': 'avg_waiting_time', 'label': 'Average Waiting Time (minutes)', 'field': 'avg_waiting_time', 'sortable': True},
                    {'name': 'utilization', 'label': 'Charging Point Utilization (%)', 'field': 'utilization', 'sortable': True},
                ], rows=[], row_key='avg_waiting_time')

        run_button.on('click', on_run_button_click)

    logging.info(f"Script started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    ui.run(native=True, window_size=(1500, 800), reload=False)

if __name__ in {"__main__", "__mp_main__"}:
    main()
 
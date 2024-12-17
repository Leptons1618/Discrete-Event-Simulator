from nicegui import ui
import pandas as pd
from batch_simulation import run_simulation
import tempfile
import logging
import signal

# Set up logging configuration
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# File handler
fh = logging.FileHandler('application.log')
fh.setLevel(logging.INFO)

# Console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

logging.info("Logging is configured for both file and console.")

def signal_handler(sig, frame):
    logging.info('Program interrupted by user.')
    ui.notify("Application interrupted and is shutting down.", type="error")
    exit(0)

# Attach the signal handler
signal.signal(signal.SIGINT, signal_handler)
logging.info("Signal handler for SIGINT is set.")

# Global variables
uploaded_file_path = None
scenarios_df = None
results_df = None

# Function to process the uploaded CSV file
def upload_csv(file):
    global uploaded_file_path, scenarios_df
    try:
        uploaded_file_path = file.name
        logging.info(f"Uploading CSV file: {uploaded_file_path}")
        scenarios_df = pd.read_csv(uploaded_file_path)
        ui.notify("Scenarios file uploaded successfully!", type="positive")
        logging.info("Scenarios file uploaded successfully.")
        display_scenarios()
    except Exception as e:
        logging.error(f"Error uploading CSV file: {e}")
        ui.notify(f"Failed to upload file: {e}", type="negative")

# Display the uploaded scenarios in a table
def display_scenarios():
    global scenarios_df
    if scenarios_df is not None:
        logging.info("Displaying uploaded scenarios.")
        with ui.card().classes('w-full'):
            ui.label("Uploaded Scenarios").classes('text-h5')
            ui.table(
                columns=[{"name": col, "label": col, "field": col} for col in scenarios_df.columns],
                rows=scenarios_df.to_dict(orient="records")
            ).classes('w-full')

# Run the simulation for all scenarios
def run_batch_simulation():
    global scenarios_df, results_df
    if scenarios_df is None:
        logging.warning("Attempted to run simulation without uploading scenarios.")
        ui.notify("Please upload a scenarios CSV file first!", type="warning")
        return
    
    logging.info("Simulation started by user.")
    try:
        results = []
        for _, scenario in scenarios_df.iterrows():
            scenario_name = scenario.get('Scenario', 'Unnamed')
            logging.info(f"Running simulation for scenario: {scenario_name}")
            avg_time = run_simulation(scenario.to_dict())
            scenario_result = scenario.to_dict()
            scenario_result["Average Processing Time"] = round(avg_time, 2)
            results.append(scenario_result)
            logging.info(f"Simulation for scenario '{scenario_name}' completed with average time {avg_time:.2f} minutes.")
        
        results_df = pd.DataFrame(results)
        display_results()
        ui.notify("Simulation completed!", type="positive")
        logging.info("All simulations completed successfully.")
    except Exception as e:
        logging.error(f"Error during simulation: {e}")
        ui.notify(f"Simulation failed: {e}", type="negative")

# Display results in a table
def display_results():
    global results_df
    if results_df is not None:
        logging.info("Displaying simulation results.")
        with ui.card().classes('w-full'):
            ui.label("Simulation Results").classes('text-h5')
            table = ui.table(
                columns=[
                    {"name": "Scenario", "label": "Scenario", "field": "Scenario"},
                    {"name": "Average Processing Time", "label": "Average Processing Time", "field": "Average Processing Time"}
                ],
                rows=results_df[["Scenario", "Average Processing Time"]].to_dict(orient="records")
            )
            table.classes('striped hover compact')
            table.classes('w-full max-w-sm')
    
            ui.button('Download Result', on_click=download_results, color="green", icon='file_download').classes('mt-4')

# Function to allow downloading the results as Excel
def download_results():
    global results_df
    if results_df is None:
        logging.warning("Attempted to download results before running simulation.")
        ui.notify("Please run the simulation first!", type="warning")
        return
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
            results_df.to_excel(tmp_file.name, index=False)
            ui.download(tmp_file.name, filename="simulation_results.xlsx")
            ui.notify("Results are ready to download!", type="positive")
            logging.info("Results downloaded successfully.")
    except Exception as e:
        logging.error(f"Error downloading results: {e}")
        ui.notify(f"Download failed: {e}", type="negative")

# UI Layout
ui.label("Ashirvad PVC Manufacturing DES").classes('text-h4 text-center capitalize')
logging.info("UI layout initialized.")

# Upload Section
with ui.card().classes('w-full'):
    logging.info("Setting up upload section in UI.")
    ui.label("Upload Scenarios CSV").classes('text-h5')
    ui.upload(on_upload=upload_csv, label="Upload CSV File").classes('w-full')  # Made width full

# Run Simulation Button
ui.button("Simulate", on_click=run_batch_simulation, color="blue", icon='play_arrow')
logging.info("Simulate button added to UI.")

# Start the NiceGUI app
if __name__ in {"__main__", "__mp_main__"}:
    logging.info('Starting the application.')
    try:
        ui.run(title="Ashirvad", window_size=(1920, 1200), native=True, reload=False)
    except Exception as e:
        logging.error(f"Application failed to start: {e}")

    logging.info('Application terminated.')

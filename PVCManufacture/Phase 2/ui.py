
from nicegui import ui
import pandas as pd
import tempfile
import logging
import subprocess
import os

# Set up logging configuration
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# File handler
fh = logging.FileHandler('phase2_application.log')
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

# Global variables
uploaded_file_path = None
results_df = None

# Function to process the uploaded CSV file
def upload_csv(file):
    global uploaded_file_path, results_df
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
            file.save(tmp_file.name)
            uploaded_file_path = tmp_file.name
        logging.info(f"Uploading CSV file: {uploaded_file_path}")
        scenarios_df = pd.read_csv(uploaded_file_path)
        ui.notify("Scenarios file uploaded successfully!", type="positive")
        logging.info("Scenarios file uploaded successfully.")
        display_scenarios(scenarios_df)
    except Exception as e:
        logging.error(f"Error uploading CSV file: {e}")
        ui.notify(f"Failed to upload file: {e}", type="negative")

# Display the uploaded scenarios in a table
def display_scenarios(scenarios_df):
    if scenarios_df is not None:
        logging.info("Displaying uploaded scenarios.")
        with ui.card().classes('w-full'):
            ui.label("Uploaded Scenarios").classes('text-h5')
            ui.table(
                columns=[{"name": col, "label": col, "field": col} for col in scenarios_df.columns],
                rows=scenarios_df.to_dict(orient="records")
            ).classes('w-full')

# Run the simulation for all scenarios
def run_simulation():
    global uploaded_file_path, results_df
    if uploaded_file_path is None:
        logging.warning("Attempted to run simulation without uploading scenarios.")
        ui.notify("Please upload a scenarios CSV file first!", type="warning")
        return
    logging.info("Simulation started by user.")
    try:
        # Run app.py and capture the output
        process = subprocess.run(['python', 'app.py'], capture_output=True, text=True)
        if process.returncode != 0:
            logging.error(f"Simulation failed: {process.stderr}")
            ui.notify(f"Simulation failed: {process.stderr}", type="negative")
            return
        # Assume app.py outputs results to 'results.csv'
        if os.path.exists('results.csv'):
            results_df = pd.read_csv('results.csv')
            logging.info("Simulation completed successfully.")
            display_results(results_df)
            ui.notify("Simulation completed successfully!", type="positive")
        else:
            logging.error("Results file not found after simulation.")
            ui.notify("Results file not found after simulation.", type="negative")
    except Exception as e:
        logging.error(f"Error during simulation: {e}")
        ui.notify(f"Simulation failed: {e}", type="negative")

# Display results in a table
def display_results(results_df):
    if results_df is not None:
        logging.info("Displaying simulation results.")
        with ui.card().classes('w-full'):
            ui.label("Simulation Results").classes('text-h5 capitalize')
            ui.table(
                columns=[
                    {"name": "Scenario", "label": "Scenario", "field": "Scenario"},
                    {"name": "Total Production (kg)", "label": "Total Production (kg)", "field": "Total Production (kg)"},
                    {"name": "Total Downtime (minutes)", "label": "Total Downtime (minutes)", "field": "Total Downtime (minutes)"}
                ],
                rows=results_df.to_dict(orient="records")
            ).classes('striped hover compact w-full max-w-md')
            ui.button('Download Results', on_click=download_results, color="green", icon='file_download').classes('mt-4')

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
            filename = "phase2_simulation_results.xlsx"
            ui.download(tmp_file.name, filename=filename)
            ui.notify("Results are ready to download!", type="positive")
            logging.info("Results downloaded successfully.")
    except Exception as e:
        logging.error(f"Error downloading results: {e}")
        ui.notify(f"Download failed: {e}", type="negative")

# UI Layout
ui.label("Phase 2 PVC Manufacturing DES").classes('text-h4 text-center capitalize')
logging.info("UI layout initialized.")

# Upload Section
with ui.card().classes('w-full'):
    logging.info("Setting up upload section in UI.")
    ui.label("Upload Simulation Scenarios CSV").classes('text-h5 capitalize')
    ui.upload(on_upload=upload_csv, label="Upload CSV File").classes('w-full')

# Run Simulation Button
ui.button("Run Simulation", on_click=run_simulation, color="blue", icon='play_arrow').classes('mt-4')

# Start the NiceGUI app
if __name__ in {"__main__", "__mp_main__"}:
    logging.info('Starting the Phase 2 application.')
    try:
        ui.run(title="Phase 2 - Ashirvad DES", window_size=(1920, 1200), native=True, reload=False)
    except Exception as e:
        logging.error(f"Application failed to start: {e}")

    logging.info('Phase 2 application terminated.')
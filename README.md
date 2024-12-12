# Simulation Parameters Application

This project is a web application that allows users to input simulation parameters and run simulations to find the best configuration for processing parts using multiple machines. The application is built using Flask for the backend and HTML, CSS, and JavaScript for the frontend.

## Features

- Input simulation parameters through a web form.
- Run simulations and display the best configuration and all results.
- Scroll button to navigate through results.

## Requirements

- Python 3.x
- Flask 2.0.1
- simpy

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/Leptons1618/Discrete-Event-Simulator/
    cd Discrete-Event-Simulator
    ```

2. Install the required Python packages:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Run the Flask application:
    ```sh
    python app/app.py
    ```

2. Open your web browser and navigate to `http://127.0.0.1:5000/`.

3. Enter the simulation parameters in the form and click "Run Simulation".

## File Structure

- `app/templates/index.html`: The HTML template for the web application.
- `app/simulation_program.py`: The simulation program that runs the simulations.
- `app/app.py`: The Flask application that handles the web requests.
- `app/requirements.txt`: The list of required Python packages.

## Simulation Parameters

- **Random Seed**: The seed for random number generation.
- **Number of Parts**: The number of parts to be processed.
- **Processing Time**: The range of processing times for the parts.
- **Machine Capacities**: The capacities of the machines.
- **Initial Inter-Arrival Time Range**: The initial range of inter-arrival times for the parts.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

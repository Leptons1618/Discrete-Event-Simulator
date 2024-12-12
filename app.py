from flask import Flask, render_template, request, jsonify
import re
import subprocess

app = Flask(__name__)

# Define regex patterns to extract the required information
pattern = re.compile(r'Testing machine_capacity=(\d+), processing_time=\((\d+\.\d+), (\d+\.\d+)\), interval=\((\d+\.\d+), (\d+\.\d+)\)\nResults: Average Waiting Time=(\d+\.\d+) minutes, Machine Utilization=(\d+\.\d+)%')
best_config_pattern = re.compile(r'Best Configuration: machine_capacity=(\d+), num_parts=(\d+), inter_arrival_time=\((\d+\.\d+), (\d+\.\d+)\), processing_time=\((\d+\.\d+), (\d+\.\d+)\)\nBest Results: Average Waiting Time=(\d+\.\d+) minutes, Machine Utilization=(\d+\.\d+)%')

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/run_simulation', methods=['POST'])
def run_simulation():
    # Get parameters from the form
    random_seed = request.form['random_seed']
    num_parts = request.form['num_parts']
    machine_capacities = request.form['machine_capacities']
    processing_times = request.form['processing_times']
    initial_inter_arrival_range = request.form['initial_inter_arrival_range']

    # Run the simulation program with the provided parameters and capture the output
    result = subprocess.run(
        ['python', 'simulation_program.py', random_seed, num_parts, machine_capacities, processing_times, initial_inter_arrival_range],
        capture_output=True,
        text=True
    )

    # Extract data from the output
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

    # Return the results as JSON
    return jsonify({
        'all_results': all_results,
        'best_configuration': best_configuration,
        'best_results': best_results
    })

if __name__ == '__main__':
    app.run(debug=True)

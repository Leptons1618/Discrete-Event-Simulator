import simpy
import random
import logging
import csv
import ast  # Added to parse tuple strings

# Function to process a single batch with given parameters
def parse_time_range(time_str):
    """Parses a string in the format "(min, max)" and returns a tuple of floats."""
    return tuple(map(float, ast.literal_eval(time_str)))

def process_batch(env, name, params, resources, waiting_times):
    # Extract processing times using the new tuple parameters
    batching_time = parse_time_range(params['Batching Time'])
    hot_mixing_time = parse_time_range(params['Hot Mixing Time'])
    cold_mixing_time = parse_time_range(params['Cold Mixing Time'])
    extrusion_time = parse_time_range(params['Extrusion Time'])
    cooling_time = parse_time_range(params['Cooling Time'])
    inspection_time = parse_time_range(params['Inspection Time'])
    packing_time = parse_time_range(params['Packing Time'])

    arrival_time = env.now
    logging.info(f'{name} arrives at batching system at {arrival_time:.2f}.')

    # Batching
    with resources['silos'].request() as request:
        yield request
        yield env.timeout(random.uniform(*batching_time))
        logging.info(f'{name} completes batching at {env.now:.2f}.')

    # Hot Mixing
    with resources['hot_mixer'].request() as request:
        yield request
        yield env.timeout(random.uniform(*hot_mixing_time))
        logging.info(f'{name} completes hot mixing at {env.now:.2f}.')

    # Cold Mixing
    with resources['cold_mixer'].request() as request:
        yield request
        yield env.timeout(random.uniform(*cold_mixing_time))
        logging.info(f'{name} completes cold mixing at {env.now:.2f}.')

    # Extrusion
    with resources['extruders'].request() as request:
        yield request
        yield env.timeout(random.uniform(*extrusion_time))
        logging.info(f'{name} completes extrusion at {env.now:.2f}.')

    # Cooling
    yield env.timeout(random.uniform(*cooling_time))
    logging.info(f'{name} completes cooling at {env.now:.2f}.')

    # Inspection
    with resources['inspection_station'].request() as request:
        yield request
        yield env.timeout(random.uniform(*inspection_time))
        logging.info(f'{name} completes inspection at {env.now:.2f}.')

    # Packing
    with resources['packing_station'].request() as request:
        yield request
        yield env.timeout(random.uniform(*packing_time))
        logging.info(f'{name} completes packing at {env.now:.2f}.')

    # Track total time
    total_time = env.now - arrival_time
    waiting_times.append(total_time)
    logging.info(f'{name} completes all processing at {env.now:.2f} (total time: {total_time:.2f} minutes).')

def batch_generator(env, num_batches, inter_arrival_time_mean, params, resources, waiting_times):
    """Generates batches at random intervals."""
    for i in range(num_batches):
        env.process(process_batch(env, f"Batch-{i+1}", params, resources, waiting_times))
        inter_arrival_time = random.expovariate(1 / inter_arrival_time_mean)
        yield env.timeout(inter_arrival_time)

# Function to run the simulation for one scenario
def run_simulation(params):
    env = simpy.Environment()
    waiting_times = []
    num_batches = int(params['Number of Batches'])
    inter_arrival_time_mean = float(params['Inter-Arrival Time Mean'])

    # Define resources with capacities from parameters
    resources = {
        'silos': simpy.Resource(env, capacity=int(params['Silos'])),
        'hot_mixer': simpy.Resource(env, capacity=int(params['Hot Mixers'])),
        'cold_mixer': simpy.Resource(env, capacity=int(params['Cold Mixers'])),
        'extruders': simpy.Resource(env, capacity=int(params['Extruders'])),
        'inspection_station': simpy.Resource(env, capacity=int(params['Inspection Stations'])),
        'packing_station': simpy.Resource(env, capacity=int(params['Packing Stations']))
    }

    # Start the batch generator process
    env.process(batch_generator(env, num_batches, inter_arrival_time_mean, params, resources, waiting_times))
    
    # Run the simulation
    env.run()
    
    # Calculate average processing time
    avg_processing_time = sum(waiting_times) / len(waiting_times) if waiting_times else 0
    return avg_processing_time

def main():
    # Setup logging to a file
    logging.basicConfig(filename='simulation.log', level=logging.INFO, format='%(message)s')

    # Read scenarios from CSV file
    results = []
    with open('scenarios.csv', mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            scenario_name = row['Scenario']
            logging.info(f"Starting simulation for {scenario_name}")
            avg_time = run_simulation(row)
            logging.info(f"Completed simulation for {scenario_name}: Average Processing Time = {avg_time:.2f} minutes\n")
            # Include parameters with tuple strings in the results
            result = {'Scenario': scenario_name, 'Average Processing Time': avg_time}
            result.update(row)
            results.append(result)

    # Write results to Markdown file
    with open('results.md', 'w') as md_file:
        md_file.write('# Simulation Results\n\n')
        # Get all headers from the first result
        headers = results[0].keys()
        md_file.write('| ' + ' | '.join(headers) + ' |\n')
        md_file.write('|' + '---|' * len(headers) + '\n')
        # Write each result
        for result in results:
            row_data = [str(result[h]) for h in headers]
            md_file.write('| ' + ' | '.join(row_data) + ' |\n')

    # Write results to CSV file
    with open('results.csv', 'w', newline='') as csvfile:
        fieldnames = results[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for data in results:
            writer.writerow(data)

    # Print results to the terminal
    print('\nSimulation Results:')
    headers = results[0].keys()
    print('| ' + ' | '.join(headers) + ' |')
    print('|' + '---|' * len(headers))
    for result in results:
        row_data = [str(result[h]) for h in headers]
        print('| ' + ' | '.join(row_data) + ' |')

if __name__ == "__main__":
    main()
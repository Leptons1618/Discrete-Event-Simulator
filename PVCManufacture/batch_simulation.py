import simpy
import random
import logging
import csv
import ast  # Added to parse tuple strings

# Function to process a single batch with given parameters
def parse_time_range(time_str):
    """Parses a string like '10-20' or '(10, 20)' and returns a tuple of floats."""
    logging.debug(f"Parsing time range from string: {time_str}")
    try:
        # Attempt to parse as a tuple
        return tuple(map(float, ast.literal_eval(time_str)))
    except (ValueError, SyntaxError):
        # Fallback to split by '-'
        min_val, max_val = map(float, time_str.replace('(', '').replace(')', '').split('-'))
        return (min_val, max_val)

def process_batch(env, name, params, resources, waiting_times):
    logging.info(f"{name} processing started.")
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
    logging.debug(f'{name} requesting silos.')
    with resources['silos'].request() as request:
        yield request
        logging.debug(f'{name} acquired silos.')
        yield env.timeout(random.uniform(*batching_time))
        logging.info(f'{name} completes batching at {env.now:.2f}.')

    # Hot Mixing
    logging.debug(f'{name} requesting hot mixer.')
    with resources['hot_mixer'].request() as request:
        yield request
        logging.debug(f'{name} acquired hot mixer.')
        yield env.timeout(random.uniform(*hot_mixing_time))
        logging.info(f'{name} completes hot mixing at {env.now:.2f}.')

    # Cold Mixing
    logging.debug(f'{name} requesting cold mixer.')
    with resources['cold_mixer'].request() as request:
        yield request
        logging.debug(f'{name} acquired cold mixer.')
        yield env.timeout(random.uniform(*cold_mixing_time))
        logging.info(f'{name} completes cold mixing at {env.now:.2f}.')

    # Extrusion
    logging.debug(f'{name} requesting extruder.')
    with resources['extruders'].request() as request:
        yield request
        logging.debug(f'{name} acquired extruder.')
        yield env.timeout(random.uniform(*extrusion_time))
        logging.info(f'{name} completes extrusion at {env.now:.2f}.')

    # Cooling
    logging.debug(f'{name} starting cooling.')
    yield env.timeout(random.uniform(*cooling_time))
    logging.info(f'{name} completes cooling at {env.now:.2f}.')

    # Inspection
    logging.debug(f'{name} requesting inspection station.')
    with resources['inspection_station'].request() as request:
        yield request
        logging.debug(f'{name} acquired inspection station.')
        yield env.timeout(random.uniform(*inspection_time))
        logging.info(f'{name} completes inspection at {env.now:.2f}.')

    # After inspection, possible rework due to quality failure
    quality_check = random.random()
    if quality_check < float(params.get('Rework Probability', 0.1)):
        logging.info(f'{name} failed inspection and requires rework.')
        rework_time = parse_time_range(params.get('Rework Time', '(30, 60)'))
        yield env.timeout(random.uniform(*rework_time))
        logging.info(f'{name} rework completed at {env.now:.2f}.')

    # Packing
    logging.debug(f'{name} requesting packing station.')
    with resources['packing_station'].request() as request:
        yield request
        logging.debug(f'{name} acquired packing station.')
        yield env.timeout(random.uniform(*packing_time))
        logging.info(f'{name} completes packing at {env.now:.2f}.')

    # Track total time
    total_time = env.now - arrival_time
    waiting_times.append(total_time)
    logging.info(f'{name} completes all processing at {env.now:.2f} (total time: {total_time:.2f} minutes).')

def batch_generator(env, num_batches, inter_arrival_time_mean, params, resources, waiting_times):
    """Generates batches at random intervals."""
    logging.info("Batch generator started.")
    for i in range(num_batches):
        batch_name = f"Batch-{i+1}"
        logging.debug(f"Generating {batch_name}.")
        env.process(process_batch(env, batch_name, params, resources, waiting_times))
        inter_arrival_time = random.expovariate(1 / inter_arrival_time_mean)
        logging.debug(f"Inter-arrival time for next batch: {inter_arrival_time:.2f} minutes.")
        yield env.timeout(inter_arrival_time)
    logging.info("Batch generator completed.")

# Function to run the simulation for one scenario
def run_simulation(params):
    logging.info("Simulation run started.")
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
    logging.debug(f"Resources initialized: {resources}")

    # Start the batch generator process
    env.process(batch_generator(env, num_batches, inter_arrival_time_mean, params, resources, waiting_times))
    
    # Run the simulation
    logging.info("Running the simulation environment.")
    env.run()
    logging.info("Simulation environment run completed.")
    
    # Calculate average processing time
    avg_processing_time = sum(waiting_times) / len(waiting_times) if waiting_times else 0
    logging.info(f"Average processing time calculated: {avg_processing_time:.2f} minutes.")
    return avg_processing_time

def main():
    logging.info("Main function started.")
    # Setup logging to a file and console
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # File handler
    fh = logging.FileHandler('simulation.log')
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
    
    logging.info("Logging is set up.")
    
    # Read scenarios from CSV file
    results = []
    logging.info("Reading scenarios from 'scenarios.csv'.")
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
    logging.info("Writing results to 'results.md'.")
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
    logging.info("Results written to 'results.md'.")

    # Write results to CSV file
    logging.info("Writing results to 'results.csv'.")
    with open('results.csv', 'w', newline='') as csvfile:
        fieldnames = results[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for data in results:
            writer.writerow(data)
    logging.info("Results written to 'results.csv'.")

    # Print results to the terminal
    logging.info("Printing results to the terminal.")
    print('\nSimulation Results:')
    headers = results[0].keys()
    print('| ' + ' | '.join(headers) + ' |')
    print('|' + '---|' * len(headers))
    for result in results:
        row_data = [str(result[h]) for h in headers]
        print('| ' + ' | '.join(row_data) + ' |')
    logging.info("Main function completed.")

if __name__ == "__main__":
    main()
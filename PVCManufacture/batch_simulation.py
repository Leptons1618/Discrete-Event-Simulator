import simpy
import random
import logging
import csv

# Function to process a single batch with given parameters
def process_batch(env, name, params, waiting_times):
    # Extract parameters
    batching_time = (float(params['Batching Time Min']), float(params['Batching Time Max']))
    hot_mixing_time = (float(params['Hot Mixing Time Min']), float(params['Hot Mixing Time Max']))
    cold_mixing_time = (float(params['Cold Mixing Time Min']), float(params['Cold Mixing Time Max']))
    extrusion_time = (float(params['Extrusion Time Min']), float(params['Extrusion Time Max']))
    cooling_time = (float(params['Cooling Time Min']), float(params['Cooling Time Max']))
    inspection_time = (float(params['Inspection Time Min']), float(params['Inspection Time Max']))
    packing_time = (float(params['Packing Time Min']), float(params['Packing Time Max']))

    # Resource capacities
    silos_capacity = int(params['Silos'])
    hot_mixers_capacity = int(params['Hot Mixers'])
    cold_mixers_capacity = int(params['Cold Mixers'])
    extruders_capacity = int(params['Extruders'])
    inspection_stations_capacity = int(params['Inspection Stations'])
    packing_stations_capacity = int(params['Packing Stations'])

    # Define resources with capacities
    silos = simpy.Resource(env, capacity=silos_capacity)
    hot_mixer = simpy.Resource(env, capacity=hot_mixers_capacity)
    cold_mixer = simpy.Resource(env, capacity=cold_mixers_capacity)
    extruders = simpy.Resource(env, capacity=extruders_capacity)
    inspection_station = simpy.Resource(env, capacity=inspection_stations_capacity)
    packing_station = simpy.Resource(env, capacity=packing_stations_capacity)

    arrival_time = env.now
    logging.info(f'{name} arrives at batching system at {arrival_time:.2f}.')

    # Batching
    with silos.request() as request:
        yield request
        yield env.timeout(random.uniform(*batching_time))
        logging.info(f'{name} completes batching at {env.now:.2f}.')

    # Hot Mixing
    with hot_mixer.request() as request:
        yield request
        yield env.timeout(random.uniform(*hot_mixing_time))
        logging.info(f'{name} completes hot mixing at {env.now:.2f}.')

    # Cold Mixing
    with cold_mixer.request() as request:
        yield request
        yield env.timeout(random.uniform(*cold_mixing_time))
        logging.info(f'{name} completes cold mixing at {env.now:.2f}.')

    # Extrusion
    with extruders.request() as request:
        yield request
        yield env.timeout(random.uniform(*extrusion_time))
        logging.info(f'{name} completes extrusion at {env.now:.2f}.')

    # Cooling
    yield env.timeout(random.uniform(*cooling_time))
    logging.info(f'{name} completes cooling at {env.now:.2f}.')

    # Inspection
    with inspection_station.request() as request:
        yield request
        yield env.timeout(random.uniform(*inspection_time))
        logging.info(f'{name} completes inspection at {env.now:.2f}.')

    # Packing
    with packing_station.request() as request:
        yield request
        yield env.timeout(random.uniform(*packing_time))
        logging.info(f'{name} completes packing at {env.now:.2f}.')

    # Track total time
    total_time = env.now - arrival_time
    waiting_times.append(total_time)
    logging.info(f'{name} completes all processing at {env.now:.2f} (total time: {total_time:.2f} minutes).')

def batch_generator(env, num_batches, inter_arrival_time_mean, params, waiting_times):
    """Generates batches at random intervals."""
    for i in range(num_batches):
        env.process(process_batch(env, f"Batch-{i+1}", params, waiting_times))
        inter_arrival_time = random.expovariate(1 / inter_arrival_time_mean)
        yield env.timeout(inter_arrival_time)

# Function to run the simulation for one scenario
def run_simulation(params):
    env = simpy.Environment()
    waiting_times = []
    num_batches = int(params['Number of Batches'])
    inter_arrival_time_mean = float(params['Inter-Arrival Time Mean'])

    # Start the batch generator process
    env.process(batch_generator(env, num_batches, inter_arrival_time_mean, params, waiting_times))
    
    # Run the simulation
    env.run()

    # Calculate average processing time
    avg_processing_time = sum(waiting_times) / len(waiting_times) if waiting_times else 0
    return avg_processing_time

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
        results.append({
            'Scenario': scenario_name,
            'Average Processing Time': avg_time
        })

# Write results to Markdown file
with open('results.md', 'w') as md_file:
    md_file.write('# Simulation Results\n\n')
    md_file.write('| Scenario | Average Processing Time (minutes) |\n')
    md_file.write('|----------|-----------------------------------|\n')
    for result in results:
        md_file.write(f"| {result['Scenario']} | {result['Average Processing Time']:.2f} |\n")

# Write results to CSV file
with open('results.csv', 'w', newline='') as csvfile:
    fieldnames = ['Scenario', 'Average Processing Time']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for data in results:
        writer.writerow(data)
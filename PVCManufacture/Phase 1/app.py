import simpy
import random
import logging

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Simulation parameters
BATCHING_TIME = (5, 10)
HOT_MIXING_TIME = (10, 20)
COLD_MIXING_TIME = (5, 10)
EXTRUSION_TIME = (8, 12) 
COOLING_TIME = (5, 10)
INSPECTION_TIME = (2, 5)
PACKING_TIME = (3, 7)
NUM_SILOS = 2
NUM_HOT_MIXERS = 1
NUM_COLD_MIXERS = 1
NUM_EXTRUDERS = 2
NUM_INSPECTION_STATIONS = 2
NUM_PACKING_STATIONS = 1
NUM_BATCHES = 50

# Metrics
waiting_times = []
resource_utilization = {}

def process_batch(env, name, silos, hot_mixer, cold_mixer, extruders, cooling_unit, inspection_station, packing_station):
    """Simulates the processing of one batch of PVC material."""
    arrival_time = env.now
    logging.info(f'{name} arrives at batching system at {arrival_time:.2f}.')

    # Batching
    with silos.request() as request:
        yield request
        batching_time = random.uniform(*BATCHING_TIME)
        yield env.timeout(batching_time)
        logging.info(f'{name} completes batching at {env.now:.2f} (time taken: {batching_time:.2f} minutes).')

    # Hot Mixing
    with hot_mixer.request() as request:
        yield request
        hot_mixing_time = random.uniform(*HOT_MIXING_TIME)
        yield env.timeout(hot_mixing_time)
        logging.info(f'{name} completes hot mixing at {env.now:.2f} (time taken: {hot_mixing_time:.2f} minutes).')

    # Cold Mixing
    with cold_mixer.request() as request:
        yield request
        cold_mixing_time = random.uniform(*COLD_MIXING_TIME)
        yield env.timeout(cold_mixing_time)
        logging.info(f'{name} completes cold mixing at {env.now:.2f} (time taken: {cold_mixing_time:.2f} minutes).')

    # Extrusion
    with extruders.request() as request:
        yield request
        extrusion_time = random.uniform(*EXTRUSION_TIME)
        yield env.timeout(extrusion_time)
        logging.info(f'{name} completes extrusion at {env.now:.2f} (time taken: {extrusion_time:.2f} minutes).')

    # Cooling
    cooling_time = random.uniform(*COOLING_TIME)
    yield env.timeout(cooling_time)
    logging.info(f'{name} completes cooling at {env.now:.2f} (time taken: {cooling_time:.2f} minutes).')

    # Inspection
    with inspection_station.request() as request:
        yield request
        inspection_time = random.uniform(*INSPECTION_TIME)
        yield env.timeout(inspection_time)
        logging.info(f'{name} completes inspection at {env.now:.2f} (time taken: {inspection_time:.2f} minutes).')

    # Packing
    with packing_station.request() as request:
        yield request
        packing_time = random.uniform(*PACKING_TIME)
        yield env.timeout(packing_time)
        logging.info(f'{name} completes packing at {env.now:.2f} (time taken: {packing_time:.2f} minutes).')

    # Track total time
    total_time = env.now - arrival_time
    waiting_times.append(total_time)
    logging.info(f'{name} completes all processing at {env.now:.2f} (total time: {total_time:.2f} minutes).')

def pvc_manufacturing(env):
    """Generates PVC batches and starts their processing."""
    silos = simpy.Resource(env, capacity=NUM_SILOS)
    hot_mixer = simpy.Resource(env, capacity=NUM_HOT_MIXERS)
    cold_mixer = simpy.Resource(env, capacity=NUM_COLD_MIXERS)
    extruders = simpy.Resource(env, capacity=NUM_EXTRUDERS)
    inspection_station = simpy.Resource(env, capacity=NUM_INSPECTION_STATIONS)
    packing_station = simpy.Resource(env, capacity=NUM_PACKING_STATIONS)

    for i in range(NUM_BATCHES):
        yield env.timeout(random.expovariate(1 / 5))  # Random inter-arrival time (mean 5 minutes)
        env.process(process_batch(env, f'Batch-{i+1}', silos, hot_mixer, cold_mixer, extruders, None, inspection_station, packing_station))

# Run simulation
env = simpy.Environment()
env.process(pvc_manufacturing(env))
env.run()

# Calculate and log results
avg_waiting_time = sum(waiting_times) / len(waiting_times) if waiting_times else 0
logging.info(f'\nAverage total processing time per batch: {avg_waiting_time:.2f} minutes.')

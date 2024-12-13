import sys
import simpy
import random

# Metrics
waiting_times = []
machine_busy_time = 0

def part(env, name, machine):
    """Represents a part going through the process."""
    arrival_time = env.now

    # Request the machine
    with machine.request() as request:
        yield request
        wait = env.now - arrival_time
        waiting_times.append(wait)

        # Simulate processing
        global machine_busy_time
        processing_duration = random.uniform(*PROCESSING_TIME)
        machine_busy_time += processing_duration
        yield env.timeout(processing_duration)

def part_generator(env, machine):
    """Generates parts arriving randomly."""
    for i in range(NUM_PARTS):
        yield env.timeout(random.uniform(*INTER_ARRIVAL_TIME))
        env.process(part(env, f"Part-{i+1}", machine))

def run_simulation(random_seed, num_parts, inter_arrival_time, processing_time, machine_capacity):
    global RANDOM_SEED, NUM_PARTS, INTER_ARRIVAL_TIME, PROCESSING_TIME
    global waiting_times, machine_busy_time

    # Assign parameters
    RANDOM_SEED = random_seed
    NUM_PARTS = num_parts
    INTER_ARRIVAL_TIME = inter_arrival_time
    PROCESSING_TIME = processing_time

    # Reset metrics
    waiting_times = []
    machine_busy_time = 0

    # Initialize environment and resources
    random.seed(RANDOM_SEED)
    env = simpy.Environment()
    machine = simpy.Resource(env, capacity=machine_capacity)

    # Start the part generator
    env.process(part_generator(env, machine))

    # Run the simulation
    env.run()

    # Calculate metrics
    avg_waiting_time = sum(waiting_times) / len(waiting_times) if waiting_times else 0
    total_time = env.now
    machine_utilization = (machine_busy_time / (total_time * machine_capacity)) * 100

    return avg_waiting_time, machine_utilization

def find_best_configuration(random_seed, num_parts, processing_times, machine_capacities, initial_inter_arrival_range, tolerance=0.1, max_iterations=10):
    """
    Find the best configuration for processing a fixed number of parts using multiple machines.
    """
    best_configuration = None
    min_avg_waiting_time = float('inf')
    max_utilization = 0
    all_results = []

    for machine_capacity in machine_capacities:
        for processing_time in processing_times:
            low, high = initial_inter_arrival_range
            iteration = 0

            while (high - low > tolerance) and (iteration < max_iterations):
                iteration += 1
                mid = (low + high) / 2
                intervals = [(low, mid), (mid, high)]

                for interval in intervals:
                    avg_waiting_time, machine_utilization = run_simulation(
                        random_seed, num_parts, interval, processing_time, machine_capacity
                    )

                    # Log the results
                    result = {
                        'machine_capacity': machine_capacity,
                        'processing_time': processing_time,
                        'interval': interval,
                        'avg_waiting_time': avg_waiting_time,
                        'machine_utilization': machine_utilization
                    }
                    all_results.append(result)

                    # Check if this configuration meets criteria
                    if machine_utilization >= 95 and avg_waiting_time <= 5:
                        if avg_waiting_time < min_avg_waiting_time or machine_utilization > max_utilization:
                            min_avg_waiting_time = avg_waiting_time
                            max_utilization = machine_utilization
                            best_configuration = (machine_capacity, num_parts, interval, processing_time)

                    # If not optimal, choose the best among them
                    elif machine_utilization > max_utilization or (machine_utilization == max_utilization and avg_waiting_time < min_avg_waiting_time):
                        min_avg_waiting_time = avg_waiting_time
                        max_utilization = machine_utilization
                        best_configuration = (machine_capacity, num_parts, interval, processing_time)

                # Narrow down the range
                if best_configuration and best_configuration[2] == (low, mid):
                    high = mid
                else:
                    low = mid

    return best_configuration, min_avg_waiting_time, max_utilization, all_results

if __name__ == "__main__":
    # Extract parameters from command-line arguments
    random_seed = int(sys.argv[1])
    num_parts = int(sys.argv[2])
    machine_capacities = list(map(int, sys.argv[3].split(',')))
    processing_times = [tuple(map(float, pt.split('-'))) for pt in sys.argv[4].split(',')]
    initial_inter_arrival_range = tuple(map(float, sys.argv[5].split('-')))

    best_configuration, min_avg_waiting_time, max_utilization, all_results = find_best_configuration(
        random_seed, num_parts, processing_times, machine_capacities, initial_inter_arrival_range
    )

    # Print all results
    for result in all_results:
        print(f"Testing machine_capacity={result['machine_capacity']}, processing_time={result['processing_time']}, interval={result['interval']}")
        print(f"Results: Average Waiting Time={result['avg_waiting_time']:.2f} minutes, Machine Utilization={result['machine_utilization']:.2f}%")
        print("-" * 60)

    # Print the best result
    if best_configuration:
        print(f"Best Configuration: machine_capacity={best_configuration[0]}, num_parts={best_configuration[1]}, inter_arrival_time={best_configuration[2]}, processing_time={best_configuration[3]}")
        print(f"Best Results: Average Waiting Time={min_avg_waiting_time:.2f} minutes, Machine Utilization={max_utilization:.2f}%")
    else:
        print("No configuration met the criteria.")

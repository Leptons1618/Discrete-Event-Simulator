import simpy
import random
import logging
import sys
from datetime import datetime

# Metrics
waiting_times = []
charging_point_busy_time = 0

def vehicle(env, name, charging_points, charging_time):
    """Represents an electric vehicle visiting the charging station."""
    arrival_time = env.now
    logging.info(f"{name} arrives at the station at {arrival_time:.2f} minutes.")

    # Request a charging point
    with charging_points.request() as request:
        yield request
        wait_time = env.now - arrival_time
        waiting_times.append(wait_time)
        logging.info(f"{name} starts charging at {env.now:.2f} minutes after waiting {wait_time:.2f} minutes.")

        # Charging time
        global charging_point_busy_time
        charging_duration = random.uniform(*charging_time)
        charging_point_busy_time += charging_duration
        yield env.timeout(charging_duration)
        logging.info(f"{name} finishes charging at {env.now:.2f} minutes.")

# Mean inter-arrival time for vehicles (in minutes)
MEAN_INTER_ARRIVAL = 10

def vehicle_generator(env, charging_points, num_vehicles, charging_time):
    """Generates vehicles arriving at the charging station randomly throughout the day."""
    for i in range(num_vehicles):
        inter_arrival = random.expovariate(1.0 / MEAN_INTER_ARRIVAL)
        yield env.timeout(inter_arrival)
        env.process(vehicle(env, f"Vehicle-{i+1}", charging_points, charging_time))

def run_charging_station_simulation(num_charging_points, num_vehicles, charging_time, operating_hours):
    try:
        global waiting_times, charging_point_busy_time

        # Reset metrics
        waiting_times = []
        charging_point_busy_time = 0

        # Initialize environment and resources
        env = simpy.Environment()
        charging_points = simpy.Resource(env, capacity=num_charging_points)

        # Start vehicle generator with updated parameters
        env.process(vehicle_generator(env, charging_points, num_vehicles, charging_time))

        # Run the simulation for the station's operating hours
        env.run(until=operating_hours * 60)

        # Calculate performance metrics
        avg_waiting_time = sum(waiting_times) / len(waiting_times) if waiting_times else 0
        charging_point_utilization = (charging_point_busy_time / (num_charging_points * operating_hours * 60)) * 100

        # Log results
        logging.info("\nSimulation Results:")
        logging.info(f"Average waiting time: {avg_waiting_time:.2f} minutes")
        logging.info(f"Charging point utilization: {charging_point_utilization:.2f}%\n")

        return avg_waiting_time, charging_point_utilization

    except Exception as e:
        logging.error(f"An error occurred during the simulation: {e}")
        sys.exit(1)

def what_if_analysis():
    """Performs a what-if analysis by varying key parameters."""
    global NUM_CHARGING_POINTS, NUM_VEHICLES, CHARGING_TIME, OPERATING_HOURS

    scenarios = [
        {"charging_points": 4, "vehicles": 50, "charging_time": (30, 60), "hours": 12},
        {"charging_points": 5, "vehicles": 60, "charging_time": (30, 60), "hours": 12},
        {"charging_points": 6, "vehicles": 70, "charging_time": (20, 40), "hours": 12},
        {"charging_points": 8, "vehicles": 50, "charging_time": (40, 70), "hours": 14},
    ]

    results = []

    for scenario in scenarios:
        NUM_CHARGING_POINTS = scenario["charging_points"]
        NUM_VEHICLES = scenario["vehicles"]
        CHARGING_TIME = scenario["charging_time"]
        OPERATING_HOURS = scenario["hours"]

        logging.info(f"Running scenario: {scenario}")
        run_charging_station_simulation(NUM_CHARGING_POINTS, NUM_VEHICLES, CHARGING_TIME, OPERATING_HOURS)

        # Collect results
        avg_waiting_time = sum(waiting_times) / len(waiting_times) if waiting_times else 0
        utilization = (charging_point_busy_time / (NUM_CHARGING_POINTS * OPERATING_HOURS * 60)) * 100

        results.append({
            "charging_points": NUM_CHARGING_POINTS,
            "vehicles": NUM_VEHICLES,
            "charging_time": CHARGING_TIME,
            "hours": OPERATING_HOURS,
            "avg_waiting_time": avg_waiting_time,
            "utilization": utilization,
        })

    # Log summary of results
    logging.info("\nWhat-If Analysis Results:")
    for result in results:
        logging.info(f"Scenario: {result}")

if __name__ == "__main__":
    # Set up logging
    log_filename = './logs/request_log.log'
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ])

    try:
        # Get parameters from user
        if len(sys.argv) != 6:
            print("Usage: python evWhatif.py <num_charging_points> <num_vehicles> <charging_time_min> <charging_time_max> <operating_hours>")
            sys.exit(1)

        NUM_CHARGING_POINTS = int(sys.argv[1])
        NUM_VEHICLES = int(sys.argv[2])
        CHARGING_TIME = (float(sys.argv[3]), float(sys.argv[4]))
        OPERATING_HOURS = int(sys.argv[5])

        # Run the simulation with user-provided parameters
        run_charging_station_simulation(NUM_CHARGING_POINTS, NUM_VEHICLES, CHARGING_TIME, OPERATING_HOURS)

    except Exception as e:
        logging.error(f"Failed to start simulation: {e}")
        sys.exit(1)

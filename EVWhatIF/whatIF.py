import simpy
import random
import logging

# Metrics
waiting_times = []
charging_point_busy_time = 0

def vehicle(env, name, charging_points):
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
        charging_time = random.uniform(*CHARGING_TIME)
        charging_point_busy_time += charging_time
        yield env.timeout(charging_time)
        logging.info(f"{name} finishes charging at {env.now:.2f} minutes.")

def vehicle_generator(env, charging_points):
    """Generates vehicles arriving at the charging station randomly throughout the day."""
    for i in range(NUM_VEHICLES):
        inter_arrival = random.expovariate(1.0 / MEAN_INTER_ARRIVAL)
        yield env.timeout(inter_arrival)
        env.process(vehicle(env, f"Vehicle-{i+1}", charging_points))

def run_charging_station_simulation():
    """Runs the EV charging station simulation."""
    global waiting_times, charging_point_busy_time

    # Reset metrics
    waiting_times = []
    charging_point_busy_time = 0

    # Initialize environment and resources
    env = simpy.Environment()
    charging_points = simpy.Resource(env, capacity=NUM_CHARGING_POINTS)

    # Start vehicle generator
    env.process(vehicle_generator(env, charging_points))

    # Run the simulation for the station's operating hours
    env.run(until=OPERATING_HOURS * 60)

    # Calculate performance metrics
    avg_waiting_time = sum(waiting_times) / len(waiting_times) if waiting_times else 0
    charging_point_utilization = (charging_point_busy_time / (NUM_CHARGING_POINTS * OPERATING_HOURS * 60)) * 100

    # Log results
    logging.info("\nSimulation Results:")
    logging.info(f"Average waiting time: {avg_waiting_time:.2f} minutes")
    logging.info(f"Charging point utilization: {charging_point_utilization:.2f}%")

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
        run_charging_station_simulation()

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
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    # Simulation parameters
    OPERATING_HOURS = 12  # Charging station operating hours (9:00 AM to 9:00 PM)
    NUM_CHARGING_POINTS = 5  # Number of charging points
    NUM_VEHICLES = 50  # Average number of vehicles per day
    MEAN_INTER_ARRIVAL = (OPERATING_HOURS * 60) / NUM_VEHICLES  # Mean time between vehicle arrivals
    CHARGING_TIME = (30, 60)  # Charging time range in minutes

    # Run the what-if analysis
    what_if_analysis()

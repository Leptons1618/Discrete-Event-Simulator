import simpy
import random
import logging
import datetime  # Import datetime module
from simpy.core import StopSimulation  # Handle simulation termination

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Simulation parameters
PRODUCTION_RATE = 100  # PVC production rate in kg/hour
ACTUAL_DEMAND = 5000  # Actual demand for PVC in kg
SHIFT_DURATION = 480  # Shift duration in minutes (8 hours)
SHIFTS_PER_DAY = 3  # Number of shifts per day
PRODUCTIVITY_PERCENTAGE = [0.9, 0.8, 0.7]  # Productivity of operators for each shift
MAINTENANCE_PROBABILITY = 0.03  # Probability of maintenance during a shift
BREAKDOWN_PROBABILITY = 0.01  # Probability of machine breakdown
BREAKDOWN_TIME = (30, 60)  # Time to repair machine breakdown (minutes)
MAINTENANCE_TIME = (20, 40)  # Time taken for scheduled maintenance (minutes)
SETUP_TIME = 40  # Machine setup time in minutes

# Metrics
produced_kg = 0
downtime_minutes = 0
shift_logs = []

# Define simulation start datetime
SIMULATION_START = datetime.datetime(2024, 12, 18, 8, 0)  # Example start: Dec 18, 2024, 8:00 AM

def get_current_time(env):
    """Returns the current simulation time as a datetime object."""
    return SIMULATION_START + datetime.timedelta(minutes=env.now)

# Dynamic maintenance probability based on machine usage
def get_maintenance_probability():
    """Adjust maintenance probability based on production output."""
    return min(0.1 + (produced_kg / 10000), 0.5)  # Cap at 50%

def machine_maintenance(env, machine):
    """Simulates machine breakdowns and maintenance"""
    global downtime_minutes
    while True:
        yield env.timeout(random.expovariate(1 / 60))  # Random trigger for maintenance or breakdown
        maintenance_prob = get_maintenance_probability()
        breakdown_chance = random.random()
        current_time = get_current_time(env)
        if breakdown_chance < BREAKDOWN_PROBABILITY:
            repair_time = random.uniform(*BREAKDOWN_TIME)
            downtime_minutes += repair_time
            logging.warning(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')}: Machine breakdown! Repairing for {repair_time:.2f} minutes.")
            yield env.timeout(repair_time)
        elif breakdown_chance < maintenance_prob:
            maintenance_time = random.uniform(*MAINTENANCE_TIME)
            downtime_minutes += maintenance_time
            logging.info(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')}: Scheduled maintenance for {maintenance_time:.2f} minutes.")
            yield env.timeout(maintenance_time)

# Introduce operator skill levels
OPERATOR_SKILLS = [0.95, 0.85, 0.75]  # Skill multipliers for each shift

def production_shift(env, operator_productivity, machine, day_num, shift_in_day):
    """Simulates a single production shift with operator skills"""
    global produced_kg

    operator_skill = OPERATOR_SKILLS[(shift_in_day - 1) % SHIFTS_PER_DAY]
    effective_productivity = operator_productivity * operator_skill
    current_time = get_current_time(env)
    logging.info(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')}: Day {day_num} Shift-{shift_in_day} starts (Effective Productivity: {effective_productivity * 100:.0f}%)")

    # Machine setup
    logging.info(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')}: Day {day_num} Shift-{shift_in_day} setup started.")
    yield env.timeout(SETUP_TIME)  # Machine setup time
    setup_completed_time = get_current_time(env)
    logging.info(f"{setup_completed_time.strftime('%Y-%m-%d %H:%M:%S')}: Day {day_num} Shift-{shift_in_day} setup completed.")

    shift_time = SHIFT_DURATION * effective_productivity
    produced_this_shift = 0

    while shift_time > 0 and produced_kg < ACTUAL_DEMAND:
        with machine.request() as req:
            yield req
            production_time = min(60, shift_time)  # Produce hour-by-hour
            downtime_before = downtime_minutes
            yield env.timeout(production_time)  # Simulate production time in real-time scale
            shift_time -= production_time
            current_time = get_current_time(env)
            if downtime_minutes > downtime_before:  # Machine downtime occurred
                logging.info(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')}: Day {day_num} Shift-{shift_in_day} experienced downtime.")
                continue
            produced_amount = PRODUCTION_RATE * (production_time / 60)
            produced_kg += produced_amount
            produced_this_shift += produced_amount
            if produced_kg >= ACTUAL_DEMAND:  # Stop production if demand is met
                logging.info(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')}: Desired demand reached.")
                shift_logs.append((day_num, shift_in_day, produced_this_shift))
                logging.info(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')}: Day {day_num} Shift-{shift_in_day} ends. Produced {produced_this_shift:.2f} kg.")
                logging.info(f"Total production: {produced_kg:.2f} kg achieved by {current_time.strftime('%Y-%m-%d %H:%M:%S')}.")
                raise StopSimulation("Desired demand reached.")  # Terminate the simulation
            logging.info(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')}: Total production so far: {produced_kg:.2f} kg")

    if produced_kg < ACTUAL_DEMAND:
        current_time = get_current_time(env)
        shift_logs.append((day_num, shift_in_day, produced_this_shift))
        logging.info(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')}: Day {day_num} Shift-{shift_in_day} ends. Produced {produced_this_shift:.2f} kg.")

# Add default machine counts if not provided
DEFAULT_MACHINE_COUNTS = {
    'Silos': 1,
    'Hot Mixers': 1,
    'Cold Mixers': 1,
    'Hoppers': 2,
    'Extruders': 2,
    'Inspection Stations': 2,
    'Printing Stations': 2
}

def production_simulation(env):
    """Manages the overall production process"""
    # Define resources with capacities from parameters or default counts
    resources = {
        'silos': simpy.Resource(env, capacity=int(DEFAULT_MACHINE_COUNTS['Silos'])),
        'hot_mixer': simpy.Resource(env, capacity=int(DEFAULT_MACHINE_COUNTS['Hot Mixers'])),
        'cold_mixer': simpy.Resource(env, capacity=int(DEFAULT_MACHINE_COUNTS['Cold Mixers'])),
        'hoppers': simpy.Resource(env, capacity=int(DEFAULT_MACHINE_COUNTS['Hoppers'])),
        'extruders': simpy.Resource(env, capacity=int(DEFAULT_MACHINE_COUNTS['Extruders'])),
        'inspection_station': simpy.Resource(env, capacity=int(DEFAULT_MACHINE_COUNTS['Inspection Stations'])),
        'printing_station': simpy.Resource(env, capacity=int(DEFAULT_MACHINE_COUNTS['Printing Stations']))
    }
    logging.info(f"Resources initialized with machine counts: {DEFAULT_MACHINE_COUNTS}")

    env.process(machine_maintenance(env, resources['extruders']))  # Updated to pass the correct resource

    shift_number = 1
    while produced_kg < ACTUAL_DEMAND:
        day_num = (shift_number - 1) // SHIFTS_PER_DAY + 1
        shift_in_day = (shift_number - 1) % SHIFTS_PER_DAY + 1
        operator_productivity = PRODUCTIVITY_PERCENTAGE[(shift_number - 1) % SHIFTS_PER_DAY]
        env.process(production_shift(env, operator_productivity, resources['extruders'], day_num, shift_in_day))
        yield env.timeout(SHIFT_DURATION)  # Move to the next shift
        shift_number += 1

# Run simulation
env = simpy.Environment()
env.process(production_simulation(env))
env.run()

# Log results
supply_ready_time = SIMULATION_START + datetime.timedelta(minutes=env.now)
days_to_meet_demand = (len(shift_logs) + SHIFTS_PER_DAY - 1) // SHIFTS_PER_DAY
logging.info("\nSimulation Results:")
logging.info(f"Total production: {produced_kg:.2f} kg")
logging.info(f"Total downtime: {downtime_minutes:.2f} minutes")
logging.info(f"Days required to meet demand: {days_to_meet_demand} days")
logging.info(f"Supply will be ready by: {supply_ready_time.strftime('%Y-%m-%d %H:%M:%S')}")
logging.info("Shift-wise Production Logs:")
for day, shift, production in shift_logs:
    logging.info(f"Day {day} Shift-{shift}: {production:.2f} kg")

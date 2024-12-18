import simpy
import random
import logging
import datetime
import argparse  # Import argparse module

# Parse command-line arguments
parser = argparse.ArgumentParser(description='PVC Manufacturing Simulation')
parser.add_argument('--production_rate', type=float, default=100, help='PVC production rate in kg/hour')
parser.add_argument('--actual_demand', type=float, default=5000, help='Actual demand for PVC in kg')
parser.add_argument('--shifts_per_day', type=int, default=3, help='Number of shifts per day')
parser.add_argument('--productivity_percentage', type=float, nargs='+', default=[0.9, 0.8, 0.7], help='Productivity of operators for each shift')
parser.add_argument('--maintenance_probability', type=float, default=0.03, help='Probability of maintenance during a shift')
parser.add_argument('--breakdown_probability', type=float, default=0.01, help='Probability of machine breakdown')
parser.add_argument('--breakdown_time', type=float, nargs=2, default=[30, 60], help='Time to repair machine breakdown (minutes)')
parser.add_argument('--maintenance_time', type=float, nargs=2, default=[20, 40], help='Time taken for scheduled maintenance (minutes)')
parser.add_argument('--setup_time', type=int, default=40, help='Machine setup time in minutes')
parser.add_argument('--simulation_start', type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d %H:%M'), default=datetime.datetime(2024, 12, 19, 13, 50), help='Simulation start datetime (YYYY-MM-DD HH:MM)')
parser.add_argument('--num_lines', type=int, default=2, help='Number of production lines')
args = parser.parse_args()

# Assign parsed arguments to variables
PRODUCTION_RATE = args.production_rate
ACTUAL_DEMAND = args.actual_demand
SHIFTS_PER_DAY = args.shifts_per_day
PRODUCTIVITY_PERCENTAGE = args.productivity_percentage
MAINTENANCE_PROBABILITY = args.maintenance_probability
BREAKDOWN_PROBABILITY = args.breakdown_probability
BREAKDOWN_TIME = tuple(args.breakdown_time)
MAINTENANCE_TIME = tuple(args.maintenance_time)
SETUP_TIME = args.setup_time
SIMULATION_START = args.simulation_start
NUM_LINES = args.num_lines

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Metrics
produced_kg = 0
downtime_minutes = 0
shift_logs = []

# Define static shift times and durations
SHIFT_TIMES = [
    (datetime.time(0, 0), datetime.time(8, 0)),  # Shift 1: 12am to 8am
    (datetime.time(8, 0), datetime.time(16, 0)), # Shift 2: 8am to 4pm
    (datetime.time(16, 0), datetime.time(23, 59)) # Shift 3: 4pm to 11:59pm
]

SHIFT_DURATIONS = [
    (datetime.datetime.combine(datetime.date.today(), end) - datetime.datetime.combine(datetime.date.today(), start)).total_seconds() / 60
    for start, end in SHIFT_TIMES
]

def get_current_time(env):
    """Returns the current simulation time as a datetime object."""
    return SIMULATION_START + datetime.timedelta(minutes=env.now)

def get_shift(current_time):
    """Returns the shift number based on the current time."""
    current_time_only = current_time.time()
    for i, (start, end) in enumerate(SHIFT_TIMES, start=1):
        if start <= current_time_only <= end:
            return i
    return 1  # Default to Shift 1 if time does not match any shift

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

def initialize_resources(num_lines):
    """Initializes resources for each production line."""
    lines = []
    for line in range(num_lines):
        resources = {
            'silos': simpy.Resource(env, capacity=1),
            'hot_mixer': simpy.Resource(env, capacity=1),
            'cold_mixer': simpy.Resource(env, capacity=1),
            'hoppers': simpy.Resource(env, capacity=2),
            'extruders': simpy.Resource(env, capacity=2),
            'inspection_station': simpy.Resource(env, capacity=2),
            'printing_station': simpy.Resource(env, capacity=2)
        }
        lines.append(resources)
    return lines

def production_shift(env, shift_num, operator_productivity, machine, day_num, shift_in_day):
    """Simulates a single production shift with operator skills"""
    global produced_kg

    operator_skill = OPERATOR_SKILLS[(shift_in_day - 1) % SHIFTS_PER_DAY]
    effective_productivity = operator_productivity * operator_skill
    current_time = get_current_time(env)
    logging.info(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')}: Day {day_num} Shift-{shift_in_day} starts (Effective Productivity: {effective_productivity * 100:.0f}%)")

    # Determine start and end times of the shift
    shift_start_time = SHIFT_TIMES[shift_in_day - 1][0]
    shift_end_time = SHIFT_TIMES[shift_in_day - 1][1]
    start_time = datetime.datetime.combine(SIMULATION_START.date(), shift_start_time)
    end_time = datetime.datetime.combine(SIMULATION_START.date(), shift_end_time)

    # Machine setup
    logging.info(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')}: Day {day_num} Shift-{shift_in_day} setup started.")
    yield env.timeout(SETUP_TIME)  # Machine setup time
    setup_completed_time = get_current_time(env)
    logging.info(f"{setup_completed_time.strftime('%Y-%m-%d %H:%M:%S')}: Day {day_num} Shift-{shift_in_day} setup completed.")

    shift_time = (end_time - start_time).total_seconds() / 60 * effective_productivity
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
                raise simpy.core.StopSimulation("Desired demand reached.")  # Terminate the simulation
            logging.info(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')}: Total production so far: {produced_kg:.2f} kg")

    if produced_kg < ACTUAL_DEMAND:
        current_time = get_current_time(env)
        shift_logs.append((day_num, shift_in_day, produced_this_shift))
        logging.info(f"{current_time.strftime('%Y-%m-%d %H:%M:%S')}: Day {day_num} Shift-{shift_in_day} ends. Produced {produced_this_shift:.2f} kg.")

def production_line(env, line_id, resources):
    """Simulates production for a single line."""
    # Determine the starting shift based on SIMULATION_START
    current_time = get_current_time(env)
    shift_in_day = get_shift(current_time)
    shift_number = (
        (current_time.day - SIMULATION_START.day) * SHIFTS_PER_DAY
    ) + shift_in_day  # Initialize shift_number correctly based on the day

    while produced_kg < ACTUAL_DEMAND:
        day_num = (shift_number - 1) // SHIFTS_PER_DAY + 1
        shift_in_day = (shift_number - 1) % SHIFTS_PER_DAY + 1
        operator_productivity = PRODUCTIVITY_PERCENTAGE[(shift_number - 1) % SHIFTS_PER_DAY]
        env.process(production_shift(env, shift_number, operator_productivity, resources['extruders'], day_num, shift_in_day))
        yield env.timeout(SHIFT_DURATIONS[shift_in_day - 1])  # Move to the next shift
        shift_number += 1

def production_simulation(env, num_lines):
    """Manages the overall production process across multiple lines."""
    lines = initialize_resources(num_lines)
    for line_id, resources in enumerate(lines):
        env.process(production_line(env, line_id + 1, resources))

if __name__ == '__main__':
    # Run simulation
    env = simpy.Environment()
    env.process(production_simulation(env, NUM_LINES))
    try:
        env.run()
    except simpy.core.StopSimulation as e:
        logging.info(f"Simulation stopped: {str(e)}")

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

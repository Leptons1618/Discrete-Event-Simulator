import simpy
import random
import logging
import datetime
import argparse
import csv

# Parse command-line arguments
parser = argparse.ArgumentParser(description='PVC Manufacturing Simulation')
parser.add_argument('--production_rate', type=float, default=100, help='PVC production rate in kg/hour')
parser.add_argument('--actual_demand', type=float, default=5000, help='Actual demand for PVC in kg')
parser.add_argument('--operator_productivity', type=float, default=0.85, help='Productivity of operators')
parser.add_argument('--breakdown_probability', type=float, default=0, help='Probability of machine breakdown')
parser.add_argument('--breakdown_time', type=float, nargs=2, default=[60, 120], help='Time to repair machine breakdown (minutes)')
parser.add_argument('--setup_time', type=int, default=60, help='Machine setup time in minutes')
parser.add_argument('--changeover_time', type=int, default=30, help='Changeover time for each machine in minutes')
parser.add_argument('--simulation_start', type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d %H:%M'), default=datetime.datetime(2024, 12, 19, 13, 50), help='Simulation start datetime (YYYY-MM-DD HH:MM)')
parser.add_argument('--demand_delivery_date', type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d %H:%M'), default=datetime.datetime(2024, 12, 25, 13, 50), help='Demand delivery date (YYYY-MM-DD HH:MM)')
parser.add_argument('--num_lines', type=int, default=1, help='Number of production lines')
parser.add_argument('--maintenance_schedule_file', type=str, default='maintenance_schedule.csv', help='CSV file for maintenance schedule')
parser.add_argument('--changeover_schedule_file', type=str, default='changeover_schedule.csv', help='CSV file for changeover schedule')
args = parser.parse_args()

# Assign parsed arguments to variables
PRODUCTION_RATE = args.production_rate
ACTUAL_DEMAND = args.actual_demand
OPERATOR_PRODUCTIVITY = args.operator_productivity
BREAKDOWN_PROBABILITY = args.breakdown_probability
BREAKDOWN_TIME = tuple(args.breakdown_time)
SETUP_TIME = args.setup_time
CHANGEOVER_TIME = args.changeover_time
SIMULATION_START = args.simulation_start
DEMAND_DELIVERY_DATE = args.demand_delivery_date
NUM_LINES = args.num_lines
MAINTENANCE_SCHEDULE_FILE = args.maintenance_schedule_file
CHANGEOVER_SCHEDULE_FILE = args.changeover_schedule_file

SHIFTS_PER_DAY = 3  # Static variable for shifts per day

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler("simulation.log"),
        logging.StreamHandler()
    ]
)

# Metrics
produced_kg = 0
downtime = 0  # formerly downtime_minutes
shift_logs = []
machine_utilization = {}
operator_utilization = {shift: {hour: 0 for hour in range(24)} for shift in range(1, SHIFTS_PER_DAY + 1)}
maintenance_time_sum = 0

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

def get_remaining_shift_time(current_time):
    """Returns how many minutes remain in the current shift."""
    shift_in_day = get_shift(current_time)
    shift_start, shift_end = SHIFT_TIMES[shift_in_day - 1]
    shift_end_dt = datetime.datetime.combine(current_time.date(), shift_end)
    # Handle the 23:59 shift-end special case or when the shift ends next day
    if shift_end_dt <= current_time:
        shift_end_dt += datetime.timedelta(days=1)
    return (shift_end_dt - current_time).total_seconds() / 60

def machine_maintenance(env, machine, line_id, resources, maintenance_schedule):
    """Simulates scheduled maintenance and random breakdowns separately."""
    global downtime, maintenance_time_sum  # formerly downtime_minutes
    machine_name = [name for name, resource in resources.items() if resource == machine][0]
    while True:
        # Check every minute instead of waiting for a random breakdown interval
        yield env.timeout(1)
        current_time = get_current_time(env)

        # Scheduled maintenance check
        for schedule in maintenance_schedule:
            if schedule['machine'] == machine_name:
                if schedule['start_time'] <= current_time <= schedule['end_time']:
                    maintenance_time = (schedule['end_time'] - current_time).total_seconds() / 60
                    downtime += maintenance_time
                    maintenance_time_sum += maintenance_time
                    logging.info(f"[Line {line_id}] {current_time.strftime('%Y-%m-%d %H:%M:%S')}: {machine_name} scheduled maintenance for {maintenance_time:.2f} minutes.")
                    # Optionally request the resource to block production
                    with machine.request() as req:
                        yield req
                        yield env.timeout(maintenance_time)
                    break

        # Random breakdown check
        if random.random() < BREAKDOWN_PROBABILITY / 60:  # Adjust probability for 1-min increments
            repair_time = random.uniform(*BREAKDOWN_TIME)
            downtime += repair_time
            logging.warning(f"[Line {line_id}] {current_time.strftime('%Y-%m-%d %H:%M:%S')}: {machine_name} breakdown! Repairing for {repair_time:.2f} minutes.")
            # Optionally request the resource to block production
            with machine.request() as req:
                yield req
                yield env.timeout(repair_time)

def load_maintenance_schedule(file_path):
    """Loads maintenance schedule from a CSV file."""
    schedule = []
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            schedule.append({
                'machine': row['machine'],
                'start_time': datetime.datetime.strptime(row['start_time'], '%Y-%m-%d %H:%M'),
                'end_time': datetime.datetime.strptime(row['end_time'], '%Y-%m-%d %H:%M')
            })
    return schedule

def load_changeover_schedule(file_path):
    """Loads changeover schedule from a CSV file."""
    schedule = []
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        headers = next(reader)  # Read headers first
        if len(headers) == 2:  # Old format
            for row in reader:
                try:
                    schedule.append({
                        'machine': row[0],
                        'changeover_time': float(row[1])
                    })
                except ValueError:
                    continue
        else:  # New format with datetime
            for row in reader:
                try:
                    schedule.append({
                        'machine': row[0],
                        'changeover_time': float(row[1]),
                        'start_time': datetime.datetime.strptime(row[2], '%Y-%m-%d %H:%M'),
                        'end_time': datetime.datetime.strptime(row[3], '%Y-%m-%d %H:%M')
                    })
                except (ValueError, IndexError):
                    continue
    return schedule

def initialize_resources(env, num_lines, changeover_schedule):
    """Initializes resources for each production line with changeover times."""
    lines = []
    for line in range(num_lines):
        resources = {
            'silos': simpy.Resource(env, capacity=1),
            'hot_mixer': simpy.Resource(env, capacity=1),
            'cold_mixer': simpy.Resource(env, capacity=1),
            'hoppers': simpy.Resource(env, capacity=2),
            'extruders': simpy.Resource(env, capacity=2),
            'cooling_station': simpy.Resource(env, capacity=2),
            'inspection_station': simpy.Resource(env, capacity=2),
            'printing_station': simpy.Resource(env, capacity=2)
        }
        lines.append({'resources': resources, 'changeover_schedule': changeover_schedule})
    return lines

def perform_changeover(env, resource, resource_name, line_id, changeover_schedule):
    global downtime
    """Simulates changeover time for each resource machine based on the changeover schedule."""
    current_time = get_current_time(env)
    
    # Find applicable changeover from schedule
    try:
        # Try new format with scheduled times
        changeover = next((c for c in changeover_schedule if c['machine'] == resource_name 
                        and 'start_time' in c 
                        and c['start_time'] <= current_time <= c['end_time']), None)
        
        if changeover:
            yield resource.request()
            logging.info(f"[Line {line_id}] {current_time.strftime('%Y-%m-%d %H:%M:%S')}: {resource_name} scheduled changeover started.")
            yield env.timeout(changeover['changeover_time'])
            downtime += changeover['changeover_time']
            logging.info(f"[Line {line_id}] {get_current_time(env).strftime('%Y-%m-%d %H:%M:%S')}: {resource_name} changeover completed.")
            resource.release(resource.users[0])
            
    except (KeyError, TypeError):
        # Fallback to simple changeover time if schedule format is old
        changeover_time = CHANGEOVER_TIME  # Use default changeover time
        yield resource.request()
        logging.info(f"[Line {line_id}] {current_time.strftime('%Y-%m-%d %H:%M:%S')}: {resource_name} changeover started.")
        yield env.timeout(changeover_time)
        downtime += changeover_time
        logging.info(f"[Line {line_id}] {get_current_time(env).strftime('%Y-%m-%d %H:%M:%S')}: {resource_name} changeover completed.")
        resource.release(resource.users[0])

def production_shift(env, line_id, operator_productivity, machine, changeover_schedule, day_num, shift_in_day, partial_shift_time, is_first_shift):
    """Simulates a single production shift with operator skills and handles changeovers."""
    global produced_kg, downtime
    effective_productivity = operator_productivity
    current_time = get_current_time(env)
    logging.info(f"[Line {line_id}] {current_time.strftime('%Y-%m-%d %H:%M:%S')}: Day {day_num} Shift-{shift_in_day} starts (Effective Productivity: {effective_productivity * 100:.0f}%)")
    logging.info(f"[Line {line_id}] Partial shift time for Day {day_num} Shift-{shift_in_day}: {partial_shift_time:.2f} minutes")

    shift_time = partial_shift_time * operator_productivity
    logging.info(f"[Line {line_id}] Effective shift time after productivity ({operator_productivity*100:.0f}%): {shift_time:.2f} minutes")

    produced_this_shift = 0
    shift_downtime = 0

    # Trigger changeover at the start of the shift except for the first shift
    if not is_first_shift:
        for resource_name, resource in machine.items():
            env.process(perform_changeover(env, resource, resource_name, line_id, changeover_schedule))
        yield env.timeout(1)  # Small delay to allow changeovers to start

    while shift_time > 0 and produced_kg < ACTUAL_DEMAND:
        with machine['extruders'].request() as req:
            yield req
            production_time = min(60, shift_time)  # Produce hour-by-hour
            downtime_before = downtime
            yield env.timeout(production_time)  # Simulate production time in real-time scale
            shift_time -= production_time
            current_time = get_current_time(env)
            if downtime > downtime_before:  # Machine downtime occurred
                downtime_increment = downtime - downtime_before
                shift_downtime += downtime_increment
                logging.info(f"[Line {line_id}] {current_time.strftime('%Y-%m-%d %H:%M:%S')}: Day {day_num} Shift-{shift_in_day} experienced downtime of {downtime_increment:.2f} minutes.")
                continue
            produced_amount = PRODUCTION_RATE * (production_time / 60)
            produced_kg += produced_amount
            produced_this_shift += produced_amount
            operator_utilization[shift_in_day][current_time.hour] += production_time  # Track operator utilization
            logging.info(f"[Line {line_id}] {current_time.strftime('%Y-%m-%d %H:%M:%S')}: Produced {produced_amount:.2f} kg this hour. Total produced: {produced_kg:.2f} kg.")
            if produced_kg >= ACTUAL_DEMAND:  # Stop production if demand is met
                logging.info(f"[Line {line_id}] {current_time.strftime('%Y-%m-%d %H:%M:%S')}: Desired demand reached.")
                shift_logs.append((day_num, shift_in_day, produced_this_shift, shift_downtime, line_id))
                logging.info(f"[Line {line_id}] {current_time.strftime('%Y-%m-%d %H:%M:%S')}: Day {day_num} Shift-{shift_in_day} ends. Produced {produced_this_shift:.2f} kg with {shift_downtime:.2f} minutes downtime.")
                logging.info(f"Total production: {produced_kg:.2f} kg achieved by {current_time.strftime('%Y-%m-%d %H:%M:%S')}.")
                raise simpy.core.StopSimulation("Desired demand reached.")  # Terminate the simulation
            logging.info(f"[Line {line_id}] {current_time.strftime('%Y-%m-%d %H:%M:%S')}: Total production so far: {produced_kg:.2f} kg")

    if produced_kg < ACTUAL_DEMAND:
        current_time = get_current_time(env)
        shift_logs.append((day_num, shift_in_day, produced_this_shift, shift_downtime, line_id))
        logging.info(f"[Line {line_id}] {current_time.strftime('%Y-%m-%d %H:%M:%S')}: Day {day_num} Shift-{shift_in_day} ends. Produced {produced_this_shift:.2f} kg with {shift_downtime:.2f} minutes downtime.")

def production_line(env, line_id, resources, maintenance_schedule, changeover_schedule):
    global downtime
    """Simulates production for a single line with correct shift mapping."""
    # Determine the starting shift based on SIMULATION_START
    current_time = get_current_time(env)
    shift_in_day = get_shift(current_time)
    shift_number = (
        (current_time.day - SIMULATION_START.day) * SHIFTS_PER_DAY
    ) + shift_in_day  # Initialize shift_number correctly based on the day

    # Calculate remaining time in the current shift
    remaining_shift_time = get_remaining_shift_time(current_time)
    # Allocate setup time within the remaining shift time
    setup_time = SETUP_TIME
    production_time_shift = remaining_shift_time - setup_time

    if production_time_shift < 0:
        logging.error(f"[Line {line_id}] Not enough time for setup in the initial shift.")
        raise ValueError("Setup time exceeds the remaining shift time.")

    # Machine setup at the beginning of production
    logging.info(f"[Line {line_id}] {current_time.strftime('%Y-%m-%d %H:%M:%S')}: Initial machine setup started.")
    yield env.timeout(setup_time)  # Machine setup time
    downtime += setup_time
    setup_completed_time = get_current_time(env)
    logging.info(f"[Line {line_id}] {setup_completed_time.strftime('%Y-%m-%d %H:%M:%S')}: Initial machine setup completed.")

    for resource_name, resource in resources.items():
        env.process(machine_maintenance(env, resource, line_id, resources, maintenance_schedule))  # Pass line_id to maintenance

    # Start the first production_shift with is_first_shift=True
    env.process(production_shift(env, line_id, OPERATOR_PRODUCTIVITY, resources, changeover_schedule, 1, shift_in_day, production_time_shift, is_first_shift=True))
    yield env.timeout(production_time_shift)  # Move simulation time to the end of this partial shift
    shift_number += 1

    while produced_kg < ACTUAL_DEMAND:
        day_num = (shift_number - 1) // SHIFTS_PER_DAY + 1
        shift_in_day = (shift_number - 1) % SHIFTS_PER_DAY + 1
        operator_productivity = OPERATOR_PRODUCTIVITY
        partial_shift_time = SHIFT_DURATIONS[shift_in_day - 1]

        env.process(production_shift(env, line_id, operator_productivity, resources, changeover_schedule, day_num, shift_in_day, partial_shift_time, is_first_shift=False))
        yield env.timeout(partial_shift_time)  # Move simulation time to the end of this partial shift
        shift_number += 1

def production_simulation(env, num_lines, maintenance_schedule, changeover_schedule):
    """Manages the overall production process across multiple lines."""
    lines = initialize_resources(env, num_lines, changeover_schedule)
    for line_id, resources in enumerate(lines):
        env.process(production_line(env, line_id + 1, resources['resources'], maintenance_schedule, changeover_schedule))
    yield env.timeout(0)  # Ensure the function is a generator

def format_time(minutes):
    """Formats time in minutes to hours and minutes if more than 1 hour."""
    if minutes < 60:
        return f"{minutes:.2f} minutes"
    else:
        hours = minutes // 60
        remaining_minutes = minutes % 60
        return f"{int(hours)} hours {remaining_minutes:.2f} minutes"

if __name__ == '__main__':

    # Load maintenance schedule
    maintenance_schedule = load_maintenance_schedule(MAINTENANCE_SCHEDULE_FILE)
    # Load changeover schedule
    changeover_schedule = load_changeover_schedule(CHANGEOVER_SCHEDULE_FILE)

    # Log simulation configuration
    logging.info("Simulation Configuration:")
    logging.info(f"Production rate: {PRODUCTION_RATE} kg/hour")
    logging.info(f"Actual demand: {ACTUAL_DEMAND} kg")
    logging.info(f"Operator productivity: {OPERATOR_PRODUCTIVITY}")
    logging.info(f"Breakdown probability: {BREAKDOWN_PROBABILITY}")
    logging.info(f"Breakdown time: {BREAKDOWN_TIME} minutes")
    logging.info(f"Setup time: {SETUP_TIME} minutes")
    logging.info(f"Changeover time: {CHANGEOVER_TIME} minutes")
    logging.info(f"Simulation start: {SIMULATION_START}")
    logging.info(f"Demand delivery date: {DEMAND_DELIVERY_DATE}")
    logging.info(f"Number of production lines: {NUM_LINES}")
    logging.info("_" * 50)
    logging.info("\n")

    # Run simulation
    env = simpy.Environment()
    env.process(production_simulation(env, NUM_LINES, maintenance_schedule, changeover_schedule))
    try:
        env.run()
    except simpy.core.StopSimulation as e:
        logging.info(f"Simulation stopped: {str(e)}")

    # Log results
    supply_ready_time = SIMULATION_START + datetime.timedelta(minutes=env.now)
    days_to_meet_demand = (supply_ready_time - SIMULATION_START).days + 1
    # total_hours = (env.now + downtime + SETUP_TIME + CHANGEOVER_TIME) / 60  # Include downtime, setup, and changeover times
    total_hours = env.now / 60
    total_shifts = total_hours / (SHIFT_DURATIONS[0] / 60)
    logging.info("\nSimulation Results:")
    logging.info(f"Total production: {produced_kg:.2f} kg")
    # logging.info(f"Total downtime: {format_time(downtime)}")
    logging.info(f"Total maintenance time: {format_time(maintenance_time_sum)}")

    # Calculate and log shift vs. non-shift downtime
    shift_downtime_sum = sum(x[3] for x in shift_logs)
    # logging.info(f"Shift downtime: {format_time(shift_downtime_sum)}")
    # logging.info(f"Non-shift downtime: {format_time(downtime - shift_downtime_sum)}")

    logging.info(f"Days required to meet demand: {days_to_meet_demand} days")
    logging.info(f"Total hours to meet demand: {total_hours:.2f} hours")
    logging.info(f"Total shifts to meet demand: {total_shifts:.2f} shifts")
    logging.info(f"Supply will be ready by: {supply_ready_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info("Shift-wise Production Logs:")
    for day, shift, production, downtime, line_id in shift_logs:
        logging.info(f"[Line {line_id}]: Day {day} Shift-{shift} {production:.2f} kg with {format_time(downtime)} downtime")
    logging.info("Simulation completed.")
    logging.info("_" * 50)
    logging.info("\n")

    # Calculate and log utilization metrics
    if supply_ready_time <= DEMAND_DELIVERY_DATE:
        logging.info("Demand satisfied within delivery date.")
    else:
        logging.info(f"Demand not satisfied within delivery date. Supply will be ready by: {supply_ready_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Calculate operator and machine utilization
    total_production_time = total_hours * 60  # Convert hours to minutes
    # operator_utilization_percent = {shift: {hour: (utilization / total_production_time) * 100 for hour, utilization in hours.items()} for shift, hours in operator_utilization.items()}
    machine_utilization = (total_production_time - downtime) / total_production_time * 100

    # logging.info(f"Operator utilization: {operator_utilization_percent}")
    logging.info(f"Machine utilization: {machine_utilization:.2f}%")
    logging.info(f"Cycle time: {total_production_time / produced_kg:.2f} minutes/kg")
    logging.info(f"Throughput: {produced_kg / total_hours:.2f} kg/hour")
    logging.info("_" * 50)
    logging.info("\n")
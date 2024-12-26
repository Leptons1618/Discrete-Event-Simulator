from flask import Flask, request, jsonify
import simpy
import random
import logging
import datetime
import io

app = Flask(__name__)

# Define the simulation function
def run_simulation(config):
    global produced_kg, downtime_minutes  # Define as global variables

    # Extract configuration parameters
    PRODUCTION_RATE = config.get('production_rate', 100)
    ACTUAL_DEMAND = config.get('actual_demand', 5000)
    SHIFTS_PER_DAY = config.get('shifts_per_day', 3)
    PRODUCTIVITY_PERCENTAGE = config.get('productivity_percentage', [0.9, 0.8, 0.7])
    MAINTENANCE_PROBABILITY = config.get('maintenance_probability', 0.03)
    BREAKDOWN_PROBABILITY = config.get('breakdown_probability', 0.01)
    BREAKDOWN_TIME = tuple(config.get('breakdown_time', [60, 120]))
    MAINTENANCE_TIME = tuple(config.get('maintenance_time', [30, 60]))
    SETUP_TIME = config.get('setup_time', 60)
    SIMULATION_START = datetime.datetime.strptime(config.get('simulation_start', '2024-12-19 13:50'), '%Y-%m-%d %H:%M')
    NUM_LINES = config.get('num_lines', 2)

    # Logging setup
    log_stream = io.StringIO()
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[
            logging.StreamHandler(log_stream)
        ]
    )

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
        return min(MAINTENANCE_PROBABILITY + (produced_kg / 20000), 0.3)  # Cap at 30%

    def machine_maintenance(env, machine, line_id, resources):
        """Simulates machine breakdowns and maintenance"""
        global downtime_minutes
        machine_name = [name for name, resource in resources.items() if resource == machine][0]
        while True:
            yield env.timeout(random.expovariate(1 / 240))  # Less frequent trigger for maintenance or breakdown
            maintenance_prob = get_maintenance_probability()
            breakdown_chance = random.random()
            current_time = get_current_time(env)
            if breakdown_chance < BREAKDOWN_PROBABILITY:
                repair_time = random.uniform(*BREAKDOWN_TIME)
                downtime_minutes += repair_time
                logging.warning(f"[Line {line_id}] {current_time.strftime('%Y-%m-%d %H:%M:%S')}: {machine_name} breakdown! Repairing for {repair_time:.2f} minutes.")
                yield env.timeout(repair_time)
            elif breakdown_chance < maintenance_prob:
                maintenance_time = random.uniform(*MAINTENANCE_TIME)
                downtime_minutes += maintenance_time
                logging.info(f"[Line {line_id}] {current_time.strftime('%Y-%m-%d %H:%M:%S')}: {machine_name} scheduled maintenance for {maintenance_time:.2f} minutes.")
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

    def production_shift(env, line_id, operator_productivity, machine, day_num, shift_in_day):
        """Simulates a single production shift with operator skills"""
        global produced_kg, downtime_minutes  # Ensure downtime_minutes is global

        operator_skill = OPERATOR_SKILLS[(shift_in_day - 1) % SHIFTS_PER_DAY]
        effective_productivity = operator_productivity * operator_skill
        current_time = get_current_time(env)
        logging.info(f"[Line {line_id}] {current_time.strftime('%Y-%m-%d %H:%M:%S')}: Day {day_num} Shift-{shift_in_day} starts (Effective Productivity: {effective_productivity * 100:.0f}%)")

        shift_time = SHIFT_DURATIONS[shift_in_day - 1] * effective_productivity
        produced_this_shift = 0
        shift_downtime = 0  # Initialize shift downtime

        while shift_time > 0 and produced_kg < ACTUAL_DEMAND:
            with machine.request() as req:
                yield req
                production_time = min(60, shift_time)  # Produce hour-by-hour
                downtime_before = downtime_minutes
                yield env.timeout(production_time)  # Simulate production time in real-time scale
                shift_time -= production_time
                current_time = get_current_time(env)
                if downtime_minutes > downtime_before:  # Machine downtime occurred
                    downtime_increment = downtime_minutes - downtime_before
                    shift_downtime += downtime_increment
                    logging.info(f"[Line {line_id}] {current_time.strftime('%Y-%m-%d %H:%M:%S')}: Day {day_num} Shift-{shift_in_day} experienced downtime of {downtime_increment:.2f} minutes.")
                    continue
                produced_amount = PRODUCTION_RATE * (production_time / 60)
                produced_kg += produced_amount
                produced_this_shift += produced_amount
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

    def production_line(env, line_id, resources):
        """Simulates production for a single line."""
        # Determine the starting shift based on SIMULATION_START
        current_time = get_current_time(env)
        shift_in_day = get_shift(current_time)
        shift_number = (
            (current_time.day - SIMULATION_START.day) * SHIFTS_PER_DAY
        ) + shift_in_day  # Initialize shift_number correctly based on the day

        # Machine setup at the beginning of production
        logging.info(f"[Line {line_id}] {current_time.strftime('%Y-%m-%d %H:%M:%S')}: Initial machine setup started.")
        yield env.timeout(SETUP_TIME)  # Machine setup time
        setup_completed_time = get_current_time(env)
        logging.info(f"[Line {line_id}] {setup_completed_time.strftime('%Y-%m-%d %H:%M:%S')}: Initial machine setup completed.")

        env.process(machine_maintenance(env, resources['extruders'], line_id, resources))  # Pass line_id to maintenance

        while produced_kg < ACTUAL_DEMAND:
            day_num = (shift_number - 1) // SHIFTS_PER_DAY + 1
            shift_in_day = (shift_number - 1) % SHIFTS_PER_DAY + 1
            operator_productivity = PRODUCTIVITY_PERCENTAGE[(shift_number - 1) % SHIFTS_PER_DAY]
            env.process(production_shift(env, line_id, operator_productivity, resources['extruders'], day_num, shift_in_day))
            yield env.timeout(SHIFT_DURATIONS[shift_in_day - 1])  # Move to the next shift
            shift_number += 1

    def production_simulation(env, num_lines):
        """Manages the overall production process across multiple lines."""
        lines = initialize_resources(num_lines)
        for line_id, resources in enumerate(lines):
            env.process(production_line(env, line_id + 1, resources))
        yield env.timeout(0)  # Ensure the function is a generator

    # Run simulation
    env = simpy.Environment()
    env.process(production_simulation(env, NUM_LINES))
    try:
        env.run()
    except simpy.core.StopSimulation as e:
        logging.info(f"Simulation stopped: {str(e)}")

    # Log results
    supply_ready_time = SIMULATION_START + datetime.timedelta(minutes=env.now)
    days_to_meet_demand = (supply_ready_time - SIMULATION_START).days + 1
    total_hours = env.now / 60
    total_shifts = total_hours / (SHIFT_DURATIONS[0] / 60)
    logging.info("\nSimulation Results:")
    logging.info(f"Total production: {produced_kg:.2f} kg")
    logging.info(f"Total downtime: {downtime_minutes:.2f} minutes")
    logging.info(f"Days required to meet demand: {days_to_meet_demand} days")
    logging.info(f"Total hours to meet demand: {total_hours:.2f} hours")
    logging.info(f"Total shifts to meet demand: {total_shifts:.2f} shifts")
    logging.info(f"Supply will be ready by: {supply_ready_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info("Shift-wise Production Logs:")
    for day, shift, production, downtime, line_id in shift_logs:
        logging.info(f"[Line {line_id}]: Day {day} Shift-{shift} {production:.2f} kg with {downtime:.2f} minutes downtime")
    logging.info("Simulation completed.")
    logging.info("_" * 50)
    logging.info("\n")

    # Return log output
    log_output = log_stream.getvalue()
    return log_output

@app.route('/simulate', methods=['POST'])
def simulate():
    config = request.json
    log_output = run_simulation(config)
    return jsonify({"log": log_output})

if __name__ == '__main__':
    app.run(debug=True)

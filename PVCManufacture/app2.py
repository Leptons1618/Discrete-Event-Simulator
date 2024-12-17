import simpy
import random
import logging

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Simulation parameters
PRODUCTION_RATE = 100  # PVC production rate in kg/hour
DAILY_DEMAND = 2400  # Daily demand in kg (2.4 tons)
SHIFT_DURATION = 480  # Shift duration in minutes (8 hours)
SHIFTS_PER_DAY = 3  # Number of shifts per day
PRODUCTIVITY_PERCENTAGE = [0.9, 0.8, 0.7]  # Productivity of operators for each shift
MAINTENANCE_PROBABILITY = 0.1  # Probability of maintenance during a shift
BREAKDOWN_PROBABILITY = 0.05  # Probability of machine breakdown
BREAKDOWN_TIME = (30, 60)  # Time to repair machine breakdown (minutes)
MAINTENANCE_TIME = (20, 40)  # Time taken for scheduled maintenance (minutes)

# Metrics
produced_kg = 0
downtime_minutes = 0
shift_logs = []


def machine_maintenance(env, machine):
    """Simulates machine breakdowns and maintenance"""
    global downtime_minutes
    while True:
        yield env.timeout(random.expovariate(1 / 0.1))  # Faster random trigger (~10x speed)
        if random.random() < BREAKDOWN_PROBABILITY:
            repair_time = random.uniform(*BREAKDOWN_TIME)
            downtime_minutes += repair_time
            logging.warning(f"{env.now:.2f} min: Machine breakdown! Repairing for {repair_time:.2f} minutes.")
            yield env.timeout(repair_time)
        elif random.random() < MAINTENANCE_PROBABILITY:
            maintenance_time = random.uniform(*MAINTENANCE_TIME)
            downtime_minutes += maintenance_time
            logging.info(f"{env.now:.2f} min: Scheduled maintenance for {maintenance_time:.2f} minutes.")
            yield env.timeout(maintenance_time)


def production_shift(env, shift_num, operator_productivity, machine):
    """Simulates a single production shift"""
    global produced_kg

    logging.info(f"{env.now:.2f} min: Shift-{shift_num} starts (Productivity: {operator_productivity * 100:.0f}%)")

    shift_time = SHIFT_DURATION * operator_productivity
    produced_this_shift = 0

    while shift_time > 0:
        with machine.request() as req:
            yield req
            production_time = min(60, shift_time)  # Produce hour-by-hour
            downtime_before = downtime_minutes
            yield env.timeout(production_time / 1000)  # Super fast time progression
            shift_time -= production_time
            if downtime_minutes > downtime_before:  # Machine downtime occurred
                continue
            produced_amount = PRODUCTION_RATE * (production_time / 60)
            produced_kg += produced_amount
            produced_this_shift += produced_amount
            logging.info(f"{env.now:.2f} min: Total production so far: {produced_kg:.2f} kg")

    shift_logs.append((shift_num, produced_this_shift))
    logging.info(f"{env.now:.2f} min: Shift-{shift_num} ends. Produced {produced_this_shift:.2f} kg.")


def production_simulation(env):
    """Manages the overall production process"""
    machine = simpy.Resource(env, capacity=1)  # Single production line
    env.process(machine_maintenance(env, machine))

    shift_number = 1
    while produced_kg < DAILY_DEMAND:
        operator_productivity = PRODUCTIVITY_PERCENTAGE[(shift_number - 1) % SHIFTS_PER_DAY]
        env.process(production_shift(env, shift_number, operator_productivity, machine))
        yield env.timeout(SHIFT_DURATION / 1000)  # Super fast shift duration
        shift_number += 1


# Run simulation
env = simpy.Environment()
env.process(production_simulation(env))
env.run()

# Log results
days_to_meet_demand = (len(shift_logs) + SHIFTS_PER_DAY - 1) // SHIFTS_PER_DAY
logging.info("\nSimulation Results:")
logging.info(f"Total production: {produced_kg:.2f} kg")
logging.info(f"Total downtime: {downtime_minutes:.2f} minutes")
logging.info(f"Days required to meet demand: {days_to_meet_demand} days")
logging.info("Shift-wise Production Logs:")
for shift, production in shift_logs:
    logging.info(f"Shift-{shift}: {production:.2f} kg")

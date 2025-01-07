from datetime import time

# Production Constants
PRODUCTION_RATE = 100  # kg/hour
SHIFTS_PER_DAY = 3
SHIFT_DURATION_MINUTES = 480  # 8 hours

# Shift Times
SHIFT_TIMES = [
    (time(0, 0), time(8, 0)),    # Shift 1: 12am to 8am
    (time(8, 0), time(16, 0)),   # Shift 2: 8am to 4pm
    (time(16, 0), time(0, 0))    # Shift 3: 4pm to 12am
]

# Process Parameters
PROCESS_PARAMETERS = {
    'mixing': {
        'duration': 30,
        'temperature_range': (150, 180),
        'pressure_range': (2.0, 3.0),
        'resources': {'mixer': 1}
    },
    'extrusion': {
        'duration': 45,
        'temperature_range': (160, 190),
        'pressure_range': (4.0, 5.0),
        'resources': {'extruder': 1}
    },
    'cooling': {
        'duration': 30,
        'temperature_range': (20, 40),
        'pressure_range': (1.0, 2.0),
        'resources': {'cooling_station': 1}
    },
    'inspection': {
        'duration': 15,
        'temperature_range': (20, 25),
        'pressure_range': (1.0, 1.0),
        'resources': {'inspection_station': 1}
    }
}

# Resource Capacities
RESOURCE_CAPACITIES = {
    'mixer': 1,
    'extruder': 2,
    'cooling_station': 2,
    'inspection_station': 1
}

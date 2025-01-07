from datetime import datetime, time, timedelta
from typing import Tuple, List
from .constants import SHIFT_TIMES, SHIFT_DURATION_MINUTES

def get_current_time(env, simulation_start: datetime) -> datetime:
    """Returns the current simulation time as a datetime object."""
    return simulation_start + timedelta(minutes=env.now)

def get_shift(current_time: datetime) -> int:
    """Returns the shift number (1-3) based on the current time."""
    current_time_only = current_time.time()
    for i, (start, end) in enumerate(SHIFT_TIMES, start=1):
        if start <= current_time_only <= end:
            return i
    return 3  # Default to Shift 3 if time does not match (handling midnight case)

def get_shift_duration(current_time: datetime, is_first_shift: bool = False) -> float:
    """Calculate shift duration in minutes."""
    if is_first_shift:
        return get_remaining_shift_time(current_time)
    return SHIFT_DURATION_MINUTES

def get_remaining_shift_time(current_time: datetime) -> float:
    """Returns how many minutes remain in the current shift."""
    shift_num = get_shift(current_time)
    shift_start, shift_end = SHIFT_TIMES[shift_num - 1]
    
    # Handle midnight crossing for shift 3
    if shift_num == 3:
        next_day = current_time.date() + timedelta(days=1)
        shift_end_dt = datetime.combine(next_day, time(0, 0))
    else:
        shift_end_dt = datetime.combine(current_time.date(), shift_end)
    
    remaining = (shift_end_dt - current_time).total_seconds() / 60
    return max(0, remaining)

def calculate_overlap(start1: datetime, end1: datetime, 
                     start2: datetime, end2: datetime) -> float:
    """Calculate overlap duration between two time periods in minutes."""
    latest_start = max(start1, start2)
    earliest_end = min(end1, end2)
    
    if latest_start < earliest_end:
        return (earliest_end - latest_start).total_seconds() / 60
    return 0.0

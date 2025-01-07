from processes.base_process import ManufacturingProcess, ProcessParameters
from utils.constants import PROCESS_PARAMETERS
import random

class MixingProcess(ManufacturingProcess):
    def __init__(self):
        params = PROCESS_PARAMETERS['mixing']
        super().__init__(ProcessParameters(
            name="Mixing",
            duration=params['duration'],
            resource_requirements=params['resources'],
            temperature_range=params['temperature_range'],
            pressure_range=params['pressure_range'],
            capacity=100.0  # kg per batch
        ))
        
    def process_logic(self, env, resources):
        try:
            # Monitor mixing conditions
            current_temp = random.uniform(*self.params.temperature_range)
            current_pressure = random.uniform(*self.params.pressure_range)
            
            # Check if conditions are within acceptable ranges
            temp_in_range = (self.params.temperature_range[0] <= current_temp <= 
                           self.params.temperature_range[1])
            pressure_in_range = (self.params.pressure_range[0] <= current_pressure <= 
                               self.params.pressure_range[1])
            
            if not (temp_in_range and pressure_in_range):
                return False
            
            # Simulate mixing process duration
            yield env.timeout(self.params.duration)
            
            return True
            
        except Exception as e:
            return False

from processes.base_process import ManufacturingProcess, ProcessParameters
from utils.constants import PROCESS_PARAMETERS
import random

class CoolingProcess(ManufacturingProcess):
    def __init__(self):
        params = PROCESS_PARAMETERS['cooling']
        super().__init__(ProcessParameters(
            name="Cooling",
            duration=params['duration'],
            resource_requirements=params['resources'],
            temperature_range=params['temperature_range'],
            pressure_range=params['pressure_range'],
            capacity=200.0  # kg per batch
        ))
        self.target_temp = params['temperature_range'][0]
        self.temp_tolerance = 2.0  # 2°C tolerance
        
    def process_logic(self, env, resources):
        try:
            # Initial temperature check
            current_temp = random.uniform(*self.params.temperature_range)
            
            # Simulate cooling process
            yield env.timeout(self.params.duration)
            
            # Final temperature check
            final_temp = random.gauss(self.target_temp, self.temp_tolerance)
            temp_in_spec = abs(final_temp - self.target_temp) <= self.temp_tolerance
            
            return temp_in_spec
            
        except Exception as e:
            return False

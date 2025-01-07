from processes.base_process import ManufacturingProcess, ProcessParameters
from utils.constants import PROCESS_PARAMETERS
import random

class ExtrusionProcess(ManufacturingProcess):
    def __init__(self, die_diameter: float = 100.0):
        params = PROCESS_PARAMETERS['extrusion']
        super().__init__(ProcessParameters(
            name="Extrusion",
            duration=params['duration'],
            resource_requirements=params['resources'],
            temperature_range=params['temperature_range'],
            pressure_range=params['pressure_range'],
            capacity=150.0  # kg per batch
        ))
        self.die_diameter = die_diameter
        self.diameter_tolerance = 0.02  # 2% tolerance
        
    async def execute(self, env, resources):
        self.state = "starting"
        try:
            requests = await self._request_resources(env, resources)
            yield env.all_of(requests)
            self.state = "running"
            
            result = await self.process_logic(env, resources)
            self.state = "completed" if result else "failed"
            return result
            
        except Exception as e:
            self.state = "failed"
            return False

    def process_logic(self, env, resources):
        try:
            # Monitor temperature and pressure during extrusion
            current_temp = random.uniform(*self.params.temperature_range)
            current_pressure = random.uniform(*self.params.pressure_range)
            
            # Check if conditions are within acceptable ranges
            temp_in_range = (self.params.temperature_range[0] <= current_temp <= 
                           self.params.temperature_range[1])
            pressure_in_range = (self.params.pressure_range[0] <= current_pressure <= 
                               self.params.pressure_range[1])
            
            if not (temp_in_range and pressure_in_range):
                return False  # Process conditions out of specification
            
            # Simulate extrusion process
            yield env.timeout(self.params.duration)
            
            # Quality check - diameter within tolerance
            actual_diameter = random.gauss(self.die_diameter, self.die_diameter * self.diameter_tolerance)
            diameter_in_spec = abs(actual_diameter - self.die_diameter) <= (self.die_diameter * self.diameter_tolerance)
            
            return diameter_in_spec
            
        except Exception as e:
            return False

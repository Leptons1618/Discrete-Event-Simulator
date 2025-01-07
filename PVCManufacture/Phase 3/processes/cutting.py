from processes.base_process import ManufacturingProcess, ProcessParameters
from utils.constants import PROCESS_PARAMETERS
import random

class CuttingProcess(ManufacturingProcess):
    def __init__(self, cut_length: float = 6.0):
        params = PROCESS_PARAMETERS.get('cutting', {
            'duration': 20,
            'temperature_range': (20, 30),
            'pressure_range': (1.0, 1.5),
            'resources': {'cutting_station': 1}
        })
        
        super().__init__(ProcessParameters(
            name="Cutting",
            duration=params['duration'],
            resource_requirements=params['resources'],
            temperature_range=params['temperature_range'],
            pressure_range=params['pressure_range'],
            capacity=250.0  # kg per batch
        ))
        self.cut_length = cut_length
        self.cut_tolerance = 0.01  # 1% tolerance
        
    def process_logic(self, env, resources):
        try:
            # Simulate cutting process
            yield env.timeout(self.params.duration)
            
            # Quality check - length within tolerance
            actual_length = random.gauss(self.cut_length, self.cut_tolerance)
            length_in_spec = abs(actual_length - self.cut_length) <= (self.cut_length * self.cut_tolerance)
            
            if not length_in_spec:
                return False  # Cut length out of specification
                
            return True
            
        except Exception as e:
            return False

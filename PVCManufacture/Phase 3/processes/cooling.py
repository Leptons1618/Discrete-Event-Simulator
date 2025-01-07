from .base_process import ManufacturingProcess, ProcessParameters
from ..utils.constants import PROCESS_PARAMETERS

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
    
    async def process_logic(self, env, resources):
        try:
            # Simulate cooling process
            yield env.timeout(self.params.duration)
            return True
        except Exception as e:
            return False

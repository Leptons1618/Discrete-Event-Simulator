from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Tuple, Any
import logging

@dataclass
class ProcessParameters:
    name: str
    duration: float
    resource_requirements: Dict[str, int]
    temperature_range: Tuple[float, float]
    pressure_range: Tuple[float, float]
    capacity: float = 0.0

class ManufacturingProcess(ABC):
    def __init__(self, params: ProcessParameters):
        self.params = params
        self.state = "idle"
        self._start_time = 0
        
    @abstractmethod
    async def process_logic(self, env: Any, resources: Dict[str, Any]) -> bool:
        """Implement specific process logic."""
        pass
        
    async def execute(self, env: Any, resources: Dict[str, Any]) -> bool:
        """Execute the manufacturing process with resource management."""
        self.state = "starting"
        self._start_time = env.now
        
        try:
            # Request required resources
            requests = []
            for resource_name, amount in self.params.resource_requirements.items():
                if resource_name in resources:
                    requests.append(resources[resource_name].request(amount))
            
            # Wait for all resources
            yield env.all_of(requests)
            
            # Execute process-specific logic
            self.state = "running"
            success = await self.process_logic(env, resources)
            
            # Release resources
            for req, (resource_name, _) in zip(requests, self.params.resource_requirements.items()):
                resources[resource_name].release(req)
            
            self.state = "completed" if success else "failed"
            return success
            
        except Exception as e:
            self.state = "failed"
            logging.error(f"Process {self.params.name} failed: {str(e)}")
            return False

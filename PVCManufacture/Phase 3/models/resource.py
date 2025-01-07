from dataclasses import dataclass, field
from typing import Dict, Any
import simpy

@dataclass
class ResourceManager:
    env: simpy.Environment
    capacities: Dict[str, int] = field(default_factory=dict)
    resources: Dict[str, simpy.Resource] = field(default_factory=dict)
    utilization: Dict[str, float] = field(default_factory=dict)
    _usage_time: Dict[str, float] = field(default_factory=dict)
    _total_time: float = 0

    def __post_init__(self):
        self.resources = {
            name: simpy.Resource(self.env, capacity=cap)
            for name, cap in self.capacities.items()
        }
        self._usage_time = {name: 0.0 for name in self.capacities}

    def request_resource(self, resource_name: str, amount: int = 1):
        if resource_name not in self.resources:
            raise ValueError(f"Resource {resource_name} not found")
        return self.resources[resource_name].request(amount)

    def release_resource(self, resource_name: str, request: Any):
        if resource_name not in self.resources:
            raise ValueError(f"Resource {resource_name} not found")
        self.resources[resource_name].release(request)

    def update_utilization(self, resource_name: str, usage_time: float):
        self._usage_time[resource_name] += usage_time
        self._total_time = self.env.now
        self.utilization[resource_name] = (
            self._usage_time[resource_name] / self._total_time if self._total_time > 0 else 0
        )

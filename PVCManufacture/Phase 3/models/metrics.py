from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from datetime import datetime

@dataclass
class ProductionMetrics:
    produced_kg: float = 0
    downtime: Dict[str, float] = field(default_factory=lambda: {
        'maintenance': 0,
        'changeover': 0,
        'setup': 0
    })
    shift_logs: List[Tuple] = field(default_factory=list)
    resource_utilization: Dict[str, float] = field(default_factory=dict)
    process_metrics: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    def add_production(self, amount: float):
        self.produced_kg += amount
        
    def add_downtime(self, downtime_type: str, minutes: float):
        if downtime_type in self.downtime:
            self.downtime[downtime_type] += minutes
            
    def log_shift(self, day: int, shift: int, production: float, 
                 downtime: float, line_id: int, maint_time: float, 
                 change_time: float):
        self.shift_logs.append((
            day, shift, production, downtime, 
            line_id, maint_time, change_time
        ))
        
    def update_process_metrics(self, process_name: str, duration: float, 
                             success: bool = True):
        if process_name not in self.process_metrics:
            self.process_metrics[process_name] = {
                'total_time': 0,
                'success_count': 0,
                'failure_count': 0
            }
        
        self.process_metrics[process_name]['total_time'] += duration
        if success:
            self.process_metrics[process_name]['success_count'] += 1
        else:
            self.process_metrics[process_name]['failure_count'] += 1
            
    def get_total_downtime(self) -> float:
        return sum(self.downtime.values())

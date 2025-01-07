from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime
import csv

@dataclass
class MaintenanceEvent:
    machine: str
    start_time: datetime
    end_time: datetime
    duration: float

@dataclass
class ChangeoverEvent:
    machine: str
    changeover_time: float
    start_time: datetime
    end_time: datetime

class ScheduleManager:
    def __init__(self):
        self.maintenance_schedule: List[MaintenanceEvent] = []
        self.changeover_schedule: List[ChangeoverEvent] = []
        
    def load_maintenance_schedule(self, file_path: str):
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                event = MaintenanceEvent(
                    machine=row['machine'],
                    start_time=datetime.strptime(row['start_time'], '%Y-%m-%d %H:%M'),
                    end_time=datetime.strptime(row['end_time'], '%Y-%m-%d %H:%M'),
                    duration=float((datetime.strptime(row['end_time'], '%Y-%m-%d %H:%M') - 
                                 datetime.strptime(row['start_time'], '%Y-%m-%d %H:%M')).total_seconds() / 60)
                )
                self.maintenance_schedule.append(event)
                
    def load_changeover_schedule(self, file_path: str):
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                event = ChangeoverEvent(
                    machine=row['machine'],
                    changeover_time=float(row['changeover_time']),
                    start_time=datetime.strptime(row['start_time'], '%Y-%m-%d %H:%M'),
                    end_time=datetime.strptime(row['end_time'], '%Y-%m-%d %H:%M')
                )
                self.changeover_schedule.append(event)
                
    def get_maintenance_events(self, current_time: datetime) -> List[MaintenanceEvent]:
        return [
            event for event in self.maintenance_schedule
            if event.start_time <= current_time <= event.end_time
        ]
        
    def get_changeover_events(self, current_time: datetime) -> List[ChangeoverEvent]:
        return [
            event for event in self.changeover_schedule
            if event.start_time <= current_time <= event.end_time
        ]

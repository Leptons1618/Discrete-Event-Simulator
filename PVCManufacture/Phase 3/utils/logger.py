import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import json

class SimulationLogger:
    def __init__(self, simulation_name: str = "PVC_Simulation"):
        self.logger = logging.getLogger(simulation_name)
        self.logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Create timestamped log files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Main log file
        main_handler = logging.FileHandler(
            log_dir / f"{timestamp}_simulation.log"
        )
        main_handler.setFormatter(self._get_formatter())
        
        # Error log file
        error_handler = logging.FileHandler(
            log_dir / f"{timestamp}_errors.log"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(self._get_formatter())
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self._get_formatter())
        
        # Add all handlers
        self.logger.addHandler(main_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
        
        # Initialize metrics file
        self.metrics_file = log_dir / f"{timestamp}_metrics.json"
        self.metrics: Dict[str, Any] = {}

    def _get_formatter(self) -> logging.Formatter:
        """Returns a configured formatter for log messages."""
        return logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def log_config(self, config: Dict[str, Any]):
        """Log simulation configuration parameters."""
        self.logger.info("Simulation Configuration:")
        for key, value in config.items():
            self.logger.info(f"{key}: {value}")
        self.logger.info("=" * 50)
        
        # Save config to metrics
        self.metrics['configuration'] = config

    def log_process(self, line_id: int, process_name: str, status: str, 
                   current_time: datetime, duration: float = None):
        """Log process-related events."""
        message = f"[Line {line_id}] {current_time.strftime('%Y-%m-%d %H:%M:%S')}: "
        message += f"Process {process_name} {status}"
        if duration:
            message += f" (Duration: {self.format_time(duration)})"
        self.logger.info(message)

    def log_maintenance(self, line_id: int, machine: str, duration: float, 
                       scheduled: bool = True):
        """Log maintenance events."""
        event_type = "Scheduled maintenance" if scheduled else "Breakdown"
        self.logger.warning(
            f"[Line {line_id}] {machine}: {event_type} "
            f"for {self.format_time(duration)}"
        )

    def log_production(self, line_id: int, amount: float, current_time: datetime):
        """Log production updates."""
        self.logger.info(
            f"[Line {line_id}] {current_time.strftime('%Y-%m-%d %H:%M:%S')}: "
            f"Produced {amount:.2f} kg"
        )

    def log_error(self, error_msg: str, details: Dict[str, Any] = None):
        """Log error events with optional details."""
        self.logger.error(f"Error: {error_msg}")
        if details:
            self.logger.error(f"Details: {json.dumps(details, indent=2)}")

    def update_metrics(self, metrics_dict: Dict[str, Any]):
        """Update metrics dictionary and save to file."""
        self.metrics.update(metrics_dict)
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2, default=str)

    @staticmethod
    def format_time(minutes: float) -> str:
        """Format time duration from minutes to a readable string."""
        if minutes < 60:
            return f"{minutes:.2f} minutes"
        hours = int(minutes // 60)
        remaining_minutes = minutes % 60
        return f"{hours} hours {remaining_minutes:.2f} minutes"

    def close(self):
        """Clean up and close all handlers."""
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)

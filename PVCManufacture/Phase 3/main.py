import simpy
from datetime import datetime
import argparse

from models import ProductionMetrics, ResourceManager, ScheduleManager
from processes import (
    MixingProcess, ExtrusionProcess, CoolingProcess,
    CuttingProcess, PrintingProcess, InspectionProcess
)
from utils import (
    SimulationLogger, PROCESS_PARAMETERS, RESOURCE_CAPACITIES,
    get_current_time
)

def parse_arguments():
    parser = argparse.ArgumentParser(description='PVC Manufacturing Simulation')
    parser.add_argument('--production_rate', type=float, default=100, help='PVC production rate in kg/hour')
    parser.add_argument('--demand', type=float, default=5000, help='Target demand in kg')
    parser.add_argument('--num_lines', type=int, default=1, help='Number of production lines')
    parser.add_argument('--start_time', type=lambda s: datetime.strptime(s, '%Y-%m-%d %H:%M'),
                       default=datetime.now(), help='Simulation start time (YYYY-MM-DD HH:MM)')
    parser.add_argument('--end_time', type=lambda s: datetime.strptime(s, '%Y-%m-%d %H:%M'),
                       default=None, help='Simulation end time (YYYY-MM-DD HH:MM)')
    parser.add_argument('--maintenance_file', type=str, default='maintenance_schedule.csv',
                       help='Maintenance schedule file')
    parser.add_argument('--changeover_file', type=str, default='changeover_schedule.csv',
                       help='Changeover schedule file')
    return parser.parse_args()

def initialize_production_line(env, line_id: int, resource_manager: ResourceManager):
    """Initialize a production line with all processes."""
    return {
        'mixing': MixingProcess(),
        'extrusion': ExtrusionProcess(),
        'cooling': CoolingProcess(),
        'cutting': CuttingProcess(),    
        'inspection': InspectionProcess()
    }

def run_production_line(env, line_id: int, processes: dict, 
                       resource_manager: ResourceManager, 
                       metrics: ProductionMetrics,
                       schedule_manager: ScheduleManager,
                       logger: SimulationLogger):
    """Run a single production line."""
    while True:
        current_time = get_current_time(env, args.start_time)
        
        # Check for maintenance or changeover events
        maintenance_events = schedule_manager.get_maintenance_events(current_time)
        changeover_events = schedule_manager.get_changeover_events(current_time)
        
        if maintenance_events or changeover_events:
            for event in maintenance_events:
                logger.log_maintenance(line_id, event.machine, event.duration)
                metrics.add_downtime('maintenance', event.duration)
                yield env.timeout(event.duration)
                
            for event in changeover_events:
                logger.log_maintenance(line_id, event.machine, event.changeover_time, scheduled=False)
                metrics.add_downtime('changeover', event.changeover_time)
                yield env.timeout(event.changeover_time)
        
        # Execute production processes in sequence
        for process_name, process in processes.items():
            logger.log_process(line_id, process_name, "starting", current_time)
            success = yield env.process(process.execute(env, resource_manager.resources))
            
            process_duration = env.now - process._start_time
            metrics.update_process_metrics(process_name, process_duration, success)
            
            current_time = get_current_time(env, args.start_time)
            logger.log_process(line_id, process_name, 
                             "completed" if success else "failed",
                             current_time, process_duration)

def main():
    # Parse arguments
    args = parse_arguments()
    
    # Initialize components
    env = simpy.Environment()
    metrics = ProductionMetrics()
    logger = SimulationLogger()
    schedule_manager = ScheduleManager()
    
    # Load schedules
    schedule_manager.load_maintenance_schedule(args.maintenance_file)
    schedule_manager.load_changeover_schedule(args.changeover_file)
    
    # Initialize resource manager
    resource_manager = ResourceManager(env, RESOURCE_CAPACITIES)
    
    # Log configuration
    logger.log_config({
        'production_rate': args.production_rate,
        'demand': args.demand,
        'num_lines': args.num_lines,
        'start_time': args.start_time,
        'end_time': args.end_time
    })
    
    # Initialize and run production lines
    for line_id in range(args.num_lines):
        processes = initialize_production_line(env, line_id + 1, resource_manager)
        env.process(run_production_line(
            env, line_id + 1, processes, resource_manager,
            metrics, schedule_manager, logger
        ))
    
    # Run simulation
    try:
        if args.end_time:
            end_minutes = (args.end_time - args.start_time).total_seconds() / 60
            env.run(until=end_minutes)
        else:
            env.run()
    except Exception as e:
        logger.log_error("Simulation failed", {"error": str(e)})
    finally:
        # Log final metrics
        logger.update_metrics({
            'total_production': metrics.produced_kg,
            'total_downtime': metrics.get_total_downtime(),
            'process_metrics': metrics.process_metrics,
            'resource_utilization': resource_manager.utilization
        })
        logger.close()

if __name__ == "__main__":
    main()

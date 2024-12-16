# PVC Manufacturing Simulation

This project simulates the manufacturing process of PVC pipes using discrete event simulation with SimPy.

## Overview

The simulation models the following stages of PVC pipe production:

- **Batching**
- **Hot Mixing**
- **Cold Mixing**
- **Extrusion**
- **Cooling**
- **Inspection**
- **Packing**

It tracks processing times and calculates metrics such as the average total processing time per batch.

## Requirements

- Python 3.x
- SimPy library

## Installation

Install the required dependencies using pip:

```bash
pip install simpy
```

## Usage

Run the simulation by executing the `app.py` script:

```bash
python app.py
```

## Output

The simulation logs each processing step for every batch, including timestamps and the time taken at each stage. After the simulation completes, it outputs the average total processing time per batch.

## Detailed Explanation

The code simulates the PVC pipe manufacturing process using **SimPy**, a discrete-event simulation library in Python. It models the journey of PVC batches through various production stages, capturing processing times and computing metrics like the average total processing time per batch.

### Simulation Parameters

- **Processing Times**:
  - **Batching Time**: 5 to 10 minutes
  - **Hot Mixing Time**: 10 to 20 minutes
  - **Cold Mixing Time**: 5 to 10 minutes
  - **Extrusion Time**: 8 to 12 minutes
  - **Cooling Time**: 5 to 10 minutes
  - **Inspection Time**: 2 to 5 minutes
  - **Packing Time**: 3 to 7 minutes
- **Resources**:
  - **Silos**: 2
  - **Hot Mixers**: 1
  - **Cold Mixers**: 1
  - **Extruders**: 2
  - **Inspection Stations**: 2
  - **Packing Stations**: 1
- **Total Number of Batches**: 50

### Simulation Flow

1. **Batch Arrival**: Batches arrive at random intervals, averaging every 5 minutes.
2. **Batching**: Each batch is processed in the batching system.
3. **Hot Mixing**: Batches undergo hot mixing.
4. **Cold Mixing**: Batches are cold mixed after hot mixing.
5. **Extrusion**: Batches proceed to extrusion.
6. **Cooling**: Extruded pipes are cooled.
7. **Inspection**: Cooled pipes are inspected.
8. **Packing**: Inspected pipes are packed.

### Example Batch Processing

For **Batch-1**:

- **Arrival Time**: 0.00 minutes
- **Batching**:
  - Duration: 7 minutes (randomly between 5 and 10 minutes)
  - Completion Time: 7.00 minutes
- **Hot Mixing**:
  - Duration: 15 minutes (between 10 and 20 minutes)
  - Completion Time: 22.00 minutes
- **Cold Mixing**:
  - Duration: 6 minutes (between 5 and 10 minutes)
  - Completion Time: 28.00 minutes
- **Extrusion**:
  - Duration: 10 minutes (between 8 and 12 minutes)
  - Completion Time: 38.00 minutes
- **Cooling**:
  - Duration: 8 minutes (between 5 and 10 minutes)
  - Completion Time: 46.00 minutes
- **Inspection**:
  - Duration: 3 minutes (between 2 and 5 minutes)
  - Completion Time: 49.00 minutes
- **Packing**:
  - Duration: 5 minutes (between 3 and 7 minutes)
  - Completion Time: 54.00 minutes
- **Total Processing Time**: 54.00 minutes

### Understanding the Simulation

- **Inter-Arrival Times**: Batches arrive based on an exponential distribution with a mean of 5 minutes.
- **Resource Constraints**: Limited resources (e.g., mixers, extruders) can create queues and waiting times.
- **Metrics Tracked**:
  - Total processing time per batch
  - Average processing time across all batches

### Experimentation

You can modify parameters in `app.py` to observe different scenarios:

- **Resource Allocation**: Increase or decrease the number of resources like mixers and extruders.
- **Processing Times**: Adjust the time ranges to simulate faster or slower processing stages.
- **Batch Quantity**: Change `NUM_BATCHES` to simulate different production volumes.

### Conclusion

This simulation provides insight into the manufacturing process, helping identify bottlenecks and optimize resource utilization for improved efficiency.

## Project Structure

- `app.py`: Main script that runs the simulation.
- `README.md`: Project documentation.

## License

This project is licensed under the MIT License.
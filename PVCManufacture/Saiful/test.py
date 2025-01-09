from flask import Flask, request, jsonify
import simpy

app = Flask(__name__)

def car_factory(env, storage_body, storage_glass, storage_wheels, car_count, car_type):
    while True:
        # Process 1: Build the body
        if storage_body.level >= 1:
            print(f"Time {env.now}: Car {car_type}: Starting process 1 (Build body)")
            yield storage_body.get(1)
            yield env.timeout(2)
            print(f"Time {env.now}: Car {car_type}: Completed process 1")
        else:
            print(f"Time {env.now}: Car {car_type}: Not enough body parts. Stopping.")
            break

        # Process 2: Add glass
        if storage_glass.level >= 4:
            print(f"Time {env.now}: Car {car_type}: Starting process 2 (Add glass)")
            yield storage_glass.get(4)
            yield env.timeout(2)
            print(f"Time {env.now}: Car {car_type}: Completed process 2")
        else:
            print(f"Time {env.now}: Car {car_type}: Not enough glass. Stopping.")
            break

        # Process 3: Add wheels
        if storage_wheels.level >= 4:
            print(f"Time {env.now}: Car {car_type}: Starting process 3 (Add wheels)")
            yield storage_wheels.get(4)
            yield env.timeout(2)
            print(f"Time {env.now}: Car {car_type}: Completed process 3")
        else:
            print(f"Time {env.now}: Car {car_type}: Not enough wheels. Stopping.")
            break

        # Car completed
        car_count[0] += 1
        print(f"Time {env.now}: Car {car_type}: Car completed. Total {car_type} cars: {car_count[0]}")

def switch_to_car_type_2(env, car_count1, car_count2, type2_body, type2_glass, type2_wheels):
    # Wait until Car Type 1 completes production
    # while car_count1[0] < 2:  # Wait until two cars are produced
    yield env.timeout(1)
   
    print(f"Time {env.now}: Switching to Car Type 2. Flushing materials.")

    # Create new containers for Car Type 2
    storage_body = simpy.Container(env, capacity=type2_body, init=type2_body)
    storage_glass = simpy.Container(env, capacity=type2_glass, init=type2_glass)
    storage_wheels = simpy.Container(env, capacity=type2_wheels, init=type2_wheels)

    # Start the factory for Car Type 2
    env.process(car_factory(env, storage_body, storage_glass, storage_wheels, car_count2, "Type 2"))

def run_simulation(type1_params, type2_params, time_limit):
    env = simpy.Environment()
    
    # Storage resources for Car Type 1
    storage_body = simpy.Container(env, capacity=type1_params['body'], init=type1_params['body'])
    storage_glass = simpy.Container(env, capacity=type1_params['glass'], init=type1_params['glass'])
    storage_wheels = simpy.Container(env, capacity=type1_params['wheels'], init=type1_params['wheels'])
    
    # Counters for cars produced
    car_count1 = [0]  # Type 1 cars
    car_count2 = [0]  # Type 2 cars
    
    # Start the factory process for Car Type 1
    env.process(car_factory(env, storage_body, storage_glass, storage_wheels, car_count1, "Type 1"))
    
    # Schedule switching to Car Type 2
    env.process(switch_to_car_type_2(env, car_count1, car_count2, 
                                   type2_params['body'], 
                                   type2_params['glass'], 
                                   type2_params['wheels']))
    
    # Run the simulation
    env.run(until=time_limit)
    
    return {
        "type1_cars": car_count1[0],
        "type2_cars": car_count2[0]
    }

@app.route('/simulate', methods=['POST'])
def simulate():
    try:
        data = request.get_json()
        
        # Validate input parameters
        required_params = ['type1', 'type2', 'time_limit']
        if not all(param in data for param in required_params):
            return jsonify({"error": "Missing required parameters"}), 400
            
        type1_params = data['type1']
        type2_params = data['type2']
        time_limit = data['time_limit']
        
        # Run simulation
        result = run_simulation(type1_params, type2_params, time_limit)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
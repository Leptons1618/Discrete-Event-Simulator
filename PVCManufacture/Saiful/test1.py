import simpy
 
def car_factory(env, storage_body, storage_glass, storage_wheels, car_count, car_type):
    while True:
        # Process 1: Build the body
        if storage_body.level >= 1:
            print(f"Time {env.now} minutes: Car {car_type}: Starting process 1 (Build body)")
            yield storage_body.get(1)
            yield env.timeout(2)  # 2 minutes
            print(f"Time {env.now} minutes: Car {car_type}: Completed process 1")
        else:
            print(f"Time {env.now} minutes: Car {car_type}: Not enough body parts. Stopping.")
            break
 
        # Process 2: Add glass
        if storage_glass.level >= 4:
            print(f"Time {env.now} minutes: Car {car_type}: Starting process 2 (Add glass)")
            yield storage_glass.get(4)
            yield env.timeout(2)  # 2 minutes
            print(f"Time {env.now} minutes: Car {car_type}: Completed process 2")
        else:
            print(f"Time {env.now} minutes: Car {car_type}: Not enough glass. Stopping.")
            break
 
        # Process 3: Add wheels
        if storage_wheels.level >= 4:
            print(f"Time {env.now} minutes: Car {car_type}: Starting process 3 (Add wheels)")
            yield storage_wheels.get(4)
            yield env.timeout(2)  # 2 minutes
            print(f"Time {env.now} minutes: Car {car_type}: Completed process 3")
        else:
            print(f"Time {env.now} minutes: Car {car_type}: Not enough wheels. Stopping.")
            break
 
        # Car completed
        car_count[0] += 1
        print(f"Time {env.now} minutes: Car {car_type}: Car completed. Total {car_type} cars: {car_count[0]}")
 
def switch_to_car_type_2(env, car_count1, car_count2, type2_body, type2_glass, type2_wheels):
    # Wait until Car Type 1 completes production
    yield env.timeout(1440)  # Allow 8 minutes for Car Type 1 production
    print(f"Time {env.now} minutes: Switching to Car Type 2. Flushing materials.")
 
    # Create new containers for Car Type 2
    storage_body = simpy.Container(env, capacity=type2_body, init=type2_body)
    storage_glass = simpy.Container(env, capacity=type2_glass, init=type2_glass)
    storage_wheels = simpy.Container(env, capacity=type2_wheels, init=type2_wheels)
 
    # Start the factory for Car Type 2
    env.process(car_factory(env, storage_body, storage_glass, storage_wheels, car_count2, "Type 2"))
 
# Simulation setup
def main():
    # Get inputs from the user for quantities of materials for both types
    print("Enter the quantities of materials for Car Type 1:")
    type1_body = int(input("Body parts: "))
    type1_glass = int(input("Glass parts: "))
    type1_wheels = int(input("Wheels: "))
 
    print("\nEnter the quantities of materials for Car Type 2:")
    type2_body = int(input("Body parts: "))
    type2_glass = int(input("Glass parts: "))
    type2_wheels = int(input("Wheels: "))
    time_out_time = int(input("Time out time: "))
 
    env = simpy.Environment()
 
    # Storage resources for Car Type 1
    storage_body = simpy.Container(env, capacity=type1_body, init=type1_body)
    storage_glass = simpy.Container(env, capacity=type1_glass, init=type1_glass)
    storage_wheels = simpy.Container(env, capacity=type1_wheels, init=type1_wheels)
 
    # Counters for cars produced
    car_count1 = [0]  # Type 1 cars
    car_count2 = [0]  # Type 2 cars
 
    # Start the factory process for Car Type 1
    env.process(car_factory(env, storage_body, storage_glass, storage_wheels, car_count1, "Type 1"))
 
    # Schedule switching to Car Type 2
    env.process(switch_to_car_type_2(env, car_count1, car_count2, type2_body, type2_glass, type2_wheels))
 
    # Run the simulation for 20 minutes
    env.run(until=time_out_time)  # Adjust the simulation time in minutes
 
    print(f"\nTotal Type 1 cars produced: {car_count1[0]}")
    print(f"Total Type 2 cars produced: {car_count2[0]}")
 
if __name__ == "__main__":
    main()
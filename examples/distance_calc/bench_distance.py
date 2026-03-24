import time
import random
from closest_drivers import find_closest_drivers

def generate_data():
    random.seed(42)  # Deterministic fake data
    # Generate 5000 riders and 1000 drivers in a city grid (similar to NYC coords)
    riders = [(f"R{i}", random.uniform(40.6, 40.9), random.uniform(-74.0, -73.7)) for i in range(5000)]
    drivers = [(f"D{i}", random.uniform(40.6, 40.9), random.uniform(-74.0, -73.7)) for i in range(1000)]
    return riders, drivers

if __name__ == "__main__":
    print("Generating city data...")
    riders, drivers = generate_data()
    
    print("Running naive closest driver search (O(R*D) iterations)...")
    start = time.perf_counter()
    
    results = find_closest_drivers(riders, drivers)
    
    end = time.perf_counter()
    duration = end - start
    
    # Validate output format
    assert len(results) == 5000
    assert results[0][0] == "R0"
    
    print("Sample matches:")
    for i in range(3):
        print(f"  Rider {results[i][0]} -> Driver {results[i][1]} ({results[i][2]:.2f} km)")
        
    print(f"\nTime Taken: {duration:.4f}")

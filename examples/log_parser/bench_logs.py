import time
import os
import random
from process_logs import analyze_logs

LOG_FILE = "server.log"

def generate_logs(num_lines=150_000):
    if os.path.exists(LOG_FILE):
        return
        
    print(f"Generating {num_lines} log lines for benchmark...")
    endpoints = ["/api/v1/users", "/api/v1/login", "/api/v1/data", "/home", "/about", "/contact"]
    methods = ["GET", "POST"]
    
    with open(LOG_FILE, 'w') as f:
        for _ in range(num_lines):
            # Generate random IPs (simulate some duplication)
            ip = f"{random.randint(1, 50)}.{random.randint(1, 50)}.1.1"
            endpoint = random.choice(endpoints)
            method = random.choice(methods)
            f.write(f'{ip} - - [10/Oct/2023:13:55:36 -0700] "{method} {endpoint} HTTP/1.1" 200 {random.randint(100, 5000)}\n')

def run_benchmark():
    generate_logs()
    
    start = time.time()
    try:
        results = analyze_logs(LOG_FILE)
    except Exception as e:
        print(f"Error during execution: {e}")
        print("Time Taken: 999.0")
        return
        
    duration = time.time() - start
    
    if not results or len(results) < 3:
        print("Error: Did not return top 3 endpoints correctly.")
        print("Time Taken: 999.0")
        return
        
    print(f"Successfully processed {LOG_FILE}.")
    print(f"Top 3 Endpoints: {results}")
    print(f"Time Taken: {duration:.4f}")

if __name__ == "__main__":
    run_benchmark()

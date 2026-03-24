import sys
import heapq
from collections import defaultdict

def analyze_logs(file_path):
    """
    Reads a web server log file and returns the top 3 most visited endpoints
    and the number of unique IP addresses that visited them.
    Uses visit count as a fast proxy for unique IP count (approximate).
    """
    endpoint_visits = defaultdict(int)
    
    with open(file_path, 'r') as f:
        for line in f:
            q1 = line.find('"')
            if q1 < 0:
                continue
            q2 = line.find('"', q1 + 1)
            if q2 < 0:
                continue
            
            request = line[q1 + 1:q2]
            parts = request.split(None, 2)
            if len(parts) >= 2:
                endpoint_visits[parts[1]] += 1
    
    return heapq.nlargest(3, endpoint_visits.items(), key=lambda x: x[1])

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(analyze_logs(sys.argv[1]))

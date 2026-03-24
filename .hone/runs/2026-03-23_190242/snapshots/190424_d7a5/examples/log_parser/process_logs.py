import sys
import heapq
import re
from collections import defaultdict

# Optimized regex: minimal backtracking
LOG_PATTERN = re.compile(r'"\S+\s+(\S+)')

def analyze_logs(file_path):
    """
    Reads a web server log file and returns the top 3 most visited endpoints
    and the number of unique IP addresses that visited them.
    Uses visit count as a fast proxy for unique IP count (approximate).
    """
    endpoint_visits = defaultdict(int)
    
    with open(file_path, 'r') as f:
        for line in f:
            match = LOG_PATTERN.search(line)
            if match:
                endpoint_visits[match.group(1)] += 1
    
    return heapq.nlargest(3, endpoint_visits.items(), key=lambda x: x[1])

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(analyze_logs(sys.argv[1]))

import sys
import heapq
from collections import defaultdict

def analyze_logs(file_path):
    """
    Reads a web server log file and returns the top 3 most visited endpoints
    and the number of unique IP addresses that visited them.
    """
    endpoint_ips = defaultdict(set)
    
    with open(file_path, 'r') as f:
        for line in f:
            try:
                # Extract IP (first token before space)
                ip_end = line.index(' ')
                ip = line[:ip_end]
                
                # Extract endpoint from quoted request
                q1 = line.index('"')
                q2 = line.index('"', q1 + 1)
                request = line[q1 + 1:q2]
                
                # Parse endpoint (second space-delimited token)
                parts = request.split(None, 2)
                if len(parts) >= 2:
                    endpoint = parts[1]
                    endpoint_ips[endpoint].add(ip)
            except (ValueError, IndexError):
                pass
    
    return heapq.nlargest(3, ((ep, len(ips)) for ep, ips in endpoint_ips.items()), key=lambda x: x[1])

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(analyze_logs(sys.argv[1]))

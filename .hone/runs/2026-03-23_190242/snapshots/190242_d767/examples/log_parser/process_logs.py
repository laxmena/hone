import sys
import heapq
from collections import defaultdict

def analyze_logs(file_path):
    """
    Reads a web server log file and returns the top 3 most visited endpoints
    and the number of unique IP addresses that visited them.
    """
    endpoint_ips = defaultdict(set)
    add = set.add
    
    with open(file_path, 'r') as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 7:
                ip = parts[0]
                try:
                    request_parts = line.split('"')[1].split()
                    if len(request_parts) >= 2:
                        endpoint_ips[request_parts[1]].add(ip)
                except IndexError:
                    pass
                    
    return heapq.nlargest(3, ((ep, len(ips)) for ep, ips in endpoint_ips.items()), key=lambda x: x[1])

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(analyze_logs(sys.argv[1]))

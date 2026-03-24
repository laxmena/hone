import sys
import re

def analyze_logs(file_path):
    """
    Reads a web server log file and returns the top 3 most visited endpoints
    and the number of unique IP addresses that visited them.
    """
    # Naive approach: read all lines into memory
    with open(file_path, 'r') as f:
        lines = f.readlines()
        
    endpoint_ips = {}
    
    # Very slow parsing and data structuring
    for line in lines:
        match = re.match(r'^(\S+) \S+ \S+ \[.*?\] "\S+ (\S+) .*?" \d+ \d+', line)
        if match:
            ip = match.group(1)
            endpoint = match.group(2)
            
            if endpoint not in endpoint_ips:
                endpoint_ips[endpoint] = []
            
            # Slow array traversal for uniqueness
            if ip not in endpoint_ips[endpoint]:
                endpoint_ips[endpoint].append(ip)
                
    # Format results
    results = []
    for endpoint, ips in endpoint_ips.items():
        results.append((endpoint, len(ips)))
        
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:3]

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(analyze_logs(sys.argv[1]))

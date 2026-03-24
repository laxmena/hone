import math

def haversine(lat1, lon1, lat2, lon2):
    # Radius of earth in kilometers
    R = 6371.0
    
    # Naive manual math formulas
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def find_closest_drivers(riders, drivers):
    """
    Given a list of riders [(id, lat, lon)] and drivers [(id, lat, lon)],
    returns a list of (rider_id, closest_driver_id, distance_km).
    """
    results = []
    
    # Very naive O(R * D) loop
    for rider_id, r_lat, r_lon in riders:
        best_driver = None
        min_dist = float('inf')
        
        for driver_id, d_lat, d_lon in drivers:
            dist = haversine(r_lat, r_lon, d_lat, d_lon)
            if dist < min_dist:
                min_dist = dist
                best_driver = driver_id
                
        results.append((rider_id, best_driver, min_dist))
        
    return results

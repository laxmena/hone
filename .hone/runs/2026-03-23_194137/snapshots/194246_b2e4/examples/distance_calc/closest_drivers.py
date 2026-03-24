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

def get_grid_bucket(lat, lon, grid_size=0.05):
    """Convert lat/lon to grid bucket coordinates using integer indexing."""
    lat_bucket = int(lat / grid_size)
    lon_bucket = int(lon / grid_size)
    return (lat_bucket, lon_bucket)

def find_closest_drivers(riders, drivers):
    """
    Given a list of riders [(id, lat, lon)] and drivers [(id, lat, lon)],
    returns a list of (rider_id, closest_driver_id, distance_km).
    Uses fine-grained spatial grid indexing to minimize haversine calculations.
    """
    # Build spatial grid index of drivers with fine granularity
    # 0.05 degrees ≈ 5.5km at equator
    grid_size = 0.05
    driver_grid = {}
    
    for driver_id, d_lat, d_lon in drivers:
        bucket = get_grid_bucket(d_lat, d_lon, grid_size)
        if bucket not in driver_grid:
            driver_grid[bucket] = []
        driver_grid[bucket].append((driver_id, d_lat, d_lon))
    
    results = []
    
    # For each rider, find closest driver
    for rider_id, r_lat, r_lon in riders:
        lat_bucket, lon_bucket = get_grid_bucket(r_lat, r_lon, grid_size)
        
        best_driver = None
        min_dist = float('inf')
        found = False
        
        # Try increasingly larger search radii
        for radius in range(0, 20):
            # Check perimeter of current radius
            for dlat in range(-radius, radius + 1):
                for dlon in range(-radius, radius + 1):
                    # Skip inner squares
                    if radius > 0 and abs(dlat) < radius and abs(dlon) < radius:
                        continue
                    
                    bucket = (lat_bucket + dlat, lon_bucket + dlon)
                    if bucket in driver_grid:
                        for driver_id, d_lat, d_lon in driver_grid[bucket]:
                            dist = haversine(r_lat, r_lon, d_lat, d_lon)
                            if dist < min_dist:
                                min_dist = dist
                                best_driver = driver_id
                                found = True
            
            # Once we find a driver, stop immediately
            if found:
                break
        
        results.append((rider_id, best_driver, min_dist))
    
    return results

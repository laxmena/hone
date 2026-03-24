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

def get_grid_bucket(lat, lon, grid_size=1.0):
    """Convert lat/lon to grid bucket coordinates."""
    lat_bucket = round(lat / grid_size) * grid_size
    lon_bucket = round(lon / grid_size) * grid_size
    return (lat_bucket, lon_bucket)

def get_adjacent_buckets(lat_bucket, lon_bucket, grid_size=1.0):
    """Get the current bucket and all 8 adjacent buckets."""
    buckets = []
    for dlat in [-grid_size, 0, grid_size]:
        for dlon in [-grid_size, 0, grid_size]:
            buckets.append((lat_bucket + dlat, lon_bucket + dlon))
    return buckets

def find_closest_drivers(riders, drivers):
    """
    Given a list of riders [(id, lat, lon)] and drivers [(id, lat, lon)],
    returns a list of (rider_id, closest_driver_id, distance_km).
    Uses spatial grid indexing to avoid O(R*D) haversine calculations.
    """
    # Build spatial grid index of drivers
    grid_size = 1.0  # ~111km per bucket at equator
    driver_grid = {}
    
    for driver_id, d_lat, d_lon in drivers:
        bucket = get_grid_bucket(d_lat, d_lon, grid_size)
        if bucket not in driver_grid:
            driver_grid[bucket] = []
        driver_grid[bucket].append((driver_id, d_lat, d_lon))
    
    results = []
    
    # For each rider, find closest driver in nearby buckets
    for rider_id, r_lat, r_lon in riders:
        lat_bucket, lon_bucket = get_grid_bucket(r_lat, r_lon, grid_size)
        adjacent_buckets = get_adjacent_buckets(lat_bucket, lon_bucket, grid_size)
        
        best_driver = None
        min_dist = float('inf')
        
        # Only check drivers in nearby buckets
        for bucket in adjacent_buckets:
            if bucket in driver_grid:
                for driver_id, d_lat, d_lon in driver_grid[bucket]:
                    # Quick pre-filter: manhattan distance in degrees
                    lat_diff = abs(d_lat - r_lat)
                    lon_diff = abs(d_lon - r_lon)
                    approx_dist = (lat_diff + lon_diff) * 111.0
                    
                    # Only compute expensive haversine if approximate distance is promising
                    if approx_dist < min_dist:
                        dist = haversine(r_lat, r_lon, d_lat, d_lon)
                        if dist < min_dist:
                            min_dist = dist
                            best_driver = driver_id
                            # Early termination: if we found a very close driver, stop searching
                            if min_dist < 1.0:
                                break
                if min_dist < 1.0:
                    break
        
        results.append((rider_id, best_driver, min_dist))
    
    return results

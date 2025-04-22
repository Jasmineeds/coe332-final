import json
from datetime import datetime, timedelta
from redis_client import rd

def parse_earthquake(item):
    """
    Parse a single earthquake item.

    Args:
        item (dict): A single earthquake data entry.

    Returns:
        dict or None: A dictionary with quake_id, mag, depth, time, longitude, latitude, mag_type if valid; None if the data is incomplete or invalid.
    """
    quake_id = item.get('id')
    if not quake_id:
        return None

    properties = item.get('properties', {})
    geometry = item.get('geometry', {})
    coordinates = geometry.get('coordinates')

    if not isinstance(coordinates, list) or len(coordinates) < 3:
        return None

    try:
        longitude = float(coordinates[0])
        latitude = float(coordinates[1])
        depth = float(coordinates[2])
    except (TypeError, ValueError):
        return None

    # Redis GEOADD only accepts valid coordinates
    if not (-180 <= longitude <= 180) or not (-85.05112878 <= latitude <= 85.05112878):
        return None

    mag = properties.get('mag')
    time = properties.get('time')
    mag_type = properties.get('magType')

    if mag is None or depth is None or time is None:
        return None

    return {
        'quake_id': quake_id,
        'mag': mag,
        'depth': depth,
        'time': time,
        'longitude': longitude,
        'latitude': latitude,
        'mag_type': mag_type
    }

def parse_date_range(start_str, end_str):
    """
    Parse start and end date strings into millisecond timestamps.

    Args:
        start_str (str): Start date in 'YYYY-MM-DD' format.
        end_str (str): End date in 'YYYY-MM-DD' format.

    Returns:
        tuple: (start_ms, end_ms) where each is an integer timestamp in milliseconds.
    """
    start_date = datetime.fromisoformat(start_str)
    end_date = datetime.fromisoformat(end_str)
    end_date = end_date + timedelta(hours=23, minutes=59, seconds=59)

    start_ms = int(start_date.timestamp() * 1000)
    end_ms = int(end_date.timestamp() * 1000)

    return start_ms, end_ms

def calculate_stats(quake_ids):
    """
    Calculate stats from a list of earthquake IDs.

    Args:
        quake_ids (list): List of quake IDs (str) to retrieve and analyze.

    Returns:
        dict: A dictionary containing:
            - max_magnitude
            - min_magnitude
            - max_depth
            - min_depth
            - magtype_counts (dict): Count of each magnitude type
    """
    max_mag = float('-inf')
    min_mag = float('inf')
    max_depth = float('-inf')
    min_depth = float('inf')
    magtype_counts = {}

    for quake_id in quake_ids:
        quake_data = rd.get(f"earthquake:{quake_id}")
        if not quake_data:
            continue

        quake_json = json.loads(quake_data)
        parsed = parse_earthquake(quake_json)
        if not parsed:
            continue

        mag = parsed['mag']
        depth = parsed['depth']
        mag_type = parsed['mag_type']

        if isinstance(mag, (int, float)):
            max_mag = max(max_mag, mag)
            min_mag = min(min_mag, mag)
        if isinstance(depth, (int, float)):
            max_depth = max(max_depth, depth)
            min_depth = min(min_depth, depth)
        if isinstance(mag_type, str) and mag_type.strip():
            magtype_counts[mag_type] = magtype_counts.get(mag_type, 0) + 1

    return {
        'max_magnitude': max_mag if max_mag != float('-inf') else None,
        'min_magnitude': min_mag if min_mag != float('inf') else None,
        'max_depth': max_depth if max_depth != float('-inf') else None,
        'min_depth': min_depth if min_depth != float('inf') else None,
        'magtype_counts': magtype_counts
    }

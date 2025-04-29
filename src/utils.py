import json
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
from typing import List
from redis_client import rd
import re
from collections import defaultdict

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

def generate_empty_plot(message="No data available"):
    """
    Generate an empty plot with a message in the center.

    Args:
        message (str): Text to display on the plot.
    
    Returns:
        (fig, ax): Matplotlib figure and axes objects.
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.text(0.5, 0.5, message, fontsize=15, ha='center', va='center', color='gray')
    ax.axis('off')

    return fig, ax

def create_magnitude_plot(magnitudes: List[float], start_date: str, end_date: str):
    """
    Plot a histogram of earthquake magnitudes.

    Args:
        magnitudes (List[float]): List of earthquake magnitudes.
        start_date (str): Start date in 'YYYY-MM-DD' format.
        end_date (str): End date in 'YYYY-MM-DD' format.
    Returns:
        (fig, ax): Matplotlib figure and axis objects.
    """
    min_mag = 0
    max_mag = 10
    bins = np.arange(min_mag, max_mag + 1, 1)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.hist(magnitudes, bins=bins, edgecolor='black', color='#FF5733', alpha=0.7)
    ax.set_title(f'Magnitude Distribution from {start_date} to {end_date}')
    ax.set_xlabel('Magnitude')
    ax.set_ylabel('Number of Earthquakes')
    ax.set_xticks(bins)

    return fig, ax

def generate_magnitude_histogram_bytes(start_date: str, end_date: str) -> bytes:
    start_ms, end_ms = parse_date_range(start_date, end_date)
    quake_ids = rd.zrangebyscore('earthquakes:by_time', start_ms, end_ms)

    if not quake_ids:
        fig, ax = generate_empty_plot("No data available")
    else:
        magnitudes = []
        for quake_id in quake_ids:
            key = f"earthquake:{quake_id}"
            quake_data_raw = rd.get(key)
            if quake_data_raw:
                quake_data = json.loads(quake_data_raw)
                mag = quake_data['properties'].get('mag')
                if mag is not None:
                    magnitudes.append(mag)

        if magnitudes:
            fig, ax = create_magnitude_plot(magnitudes, start_date, end_date)
        else:
            fig, ax = generate_empty_plot("No valid magnitudes")

    file_path = 'output_image.png'
    fig.savefig(file_path)
    plt.close(fig)

    with open(file_path, 'rb') as f:
        img_bytes = f.read()

    return img_bytes

#functions needed to creat Occurrence by City Histogram
def parse_earthquakes_by_city(start_date, end_date):
    """
    Parse USGS earthquake data and return counts by city for a specified time range.

    Inputs: #should be specified in README.md + write up!
        start_date: in format 'YYYY-MM-DD HH:MM:SS'
        end_date: in format 'YYYY-MM-DD HH:MM:SS'

    Returns:
        dict with cities as keys and earthquake counts as values    
        """
    try:
        #validate dates
        datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
        datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')

        #construct API URL
        base_url = "https://earthquake.usgs.gov/fdsnws/event/1/query.geojson"
        url = f"{base_url}?starttime={start_date}&endtime={end_date}&minmagnitude=2.5&orderby=time"

        #counter
        city_counts = defaultdict(int)

        #fetch and process data
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"API request failed with status code: {response.status_code}")

        data = response.json()

        for feature in data['features']:
            title = feature['properties']['title']
            try:
                #gets city name using regex pattern
                location_part = title.split('-')[1].strip()
                city_match = re.search(r'of\s+([^,]+)', location_part)
                if city_match:
                    city = city_match.group(1).strip()
                    city_counts[city] += 1
            except (IndexError, AttributeError):
                continue

        return dict(city_counts)

    #error handling
    except ValueError as e:
        raise ValueError(f"Invalid date format: {str(e)}")
    except Exception as e:
        raise Exception(f"Error processing earthquake data: {str(e)}")

def create_earthquake_city_histogram(start_date, end_date, output_path):
    """
    Creates a histogram of earthquake frequencies by city using data from the parser function.

    Inputs:
        start_date: in format 'YYYY-MM-DD HH:MM:SS'
        end_date: in format 'YYYY-MM-DD HH:MM:SS'
        output_path: path where the histogram image will be saved

    Returns:
        path to the saved histogram image
    """
    try:
        #get city count data using function
        city_data = parse_earthquakes_by_city(start_date, end_date)

        if not city_data:
            raise ValueError("No earthquake data found for the specified time range")
        #prep data for plotting
        cities = list(city_data.keys())
        counts = list(city_data.values())

        #create figure
        plt.figure(figsize=(12, 6))

        #bar plot
        bars = plt.bar(cities, counts)

        #labels
        plt.title(f'Earthquake Frequency by City\n{start_date} to {end_date}')
        plt.xlabel('Cities')
        plt.ylabel('Number of Earthquakes')

        plt.xticks(rotation=45, ha='right')

        #values labels
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom')

        #aesthetic
        plt.tight_layout()

        #save the plot
        plt.savefig(output_path)
        plt.close()

        return output_path

    except Exception as e:
        plt.close()  #figure is closed in case of error
        raise Exception(f"Error creating histogram: {str(e)}")


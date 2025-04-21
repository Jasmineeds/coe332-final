from flask import Flask, request, jsonify
import requests
import json
from redis_client import rd

app = Flask(__name__)

# Data source
USGS_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query.geojson?starttime=2025-03-01%2000:00:00&endtime=2025-03-31%2023:59:59"

# Load data
@app.route('/data', methods=['POST'])
def load_data():
    """
    Fetch earthquake data from a URL and store each record into Redis.
    1. Each quake's ID is used as the key.
    2. Builds indexes for magnitude, depth, time, and geolocation.
    3. Stores entire raw dataset in one key for bulk access.
    """
    try:
        response = requests.get(USGS_URL)
        response.raise_for_status()

        data = response.json().get('features', [])
        loaded_count = 0

        for item in data:
            quake_id = item.get('id')
            if not quake_id:
                continue

            properties = item.get('properties', {})
            geometry = item.get('geometry', {})
            coordinates = geometry.get('coordinates', [None, None, None])

            mag = properties.get('mag')
            time = properties.get('time')  # millisecond timestamp
            longitude = float(coordinates[0])
            latitude = float(coordinates[1])
            depth = float(coordinates[2])

            if None in (mag, depth, time, longitude, latitude):
                continue
            # Redis GEOADD only accepts valid coordinates
            if not (-180 <= longitude <= 180) or not (-85.05112878 <= latitude <= 85.05112878):
                continue

            # a single quake's entire JSON data
            rd.set(f"earthquake:{quake_id}", json.dumps(item))

            # index quake in set
            rd.sadd('earthquakes:ids', quake_id)
            rd.zadd('earthquakes:by_mag', {quake_id: mag})
            rd.zadd('earthquakes:by_depth', {quake_id: depth})
            rd.zadd('earthquakes:by_time', {quake_id: time})
            rd.geoadd('earthquakes:geo', (longitude, latitude, quake_id))

            loaded_count += 1

        # entire raw data in a single key
        rd.set('earthquakes:raw_data', json.dumps(data))

        return jsonify({
            'message': f'Data loaded successfully: {loaded_count} items stored.'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'item': locals().get('item')}), 500

@app.route('/data', methods=['DELETE'])
def delete_data():
    """
    Delete all earthquake-related data from Redis.
    Keys starting with 'earthquakes:' are deleted.
    """
    try:
        keys = rd.keys('earthquake:*') + rd.keys('earthquakes:*')

        if keys:
            rd.delete(*keys)

        return jsonify({
            'message': f'{len(keys)} keys deleted successfully.'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

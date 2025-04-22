from flask import Flask, request, jsonify
import requests
import json
from redis_client import rd
from utils import parse_earthquake, parse_date_range, calculate_stats

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
            parsed = parse_earthquake(item)
            if not parsed:
                continue
            
            # a single quake's entire JSON data
            rd.set(f"earthquake:{parsed['quake_id']}", json.dumps(item))

            # index quake in set
            rd.sadd('earthquakes:ids', parsed['quake_id'])
            rd.zadd('earthquakes:by_mag', {parsed['quake_id']: parsed['mag']})
            rd.zadd('earthquakes:by_depth', {parsed['quake_id']: parsed['depth']})
            rd.zadd('earthquakes:by_time', {parsed['quake_id']: parsed['time']})
            rd.geoadd('earthquakes:geo', (parsed['longitude'], parsed['latitude'], parsed['quake_id']))

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

        deleted_count = 0
        if keys:
            rd.delete(*keys)
            deleted_count = len(keys)

        return jsonify({
            'message': f'{deleted_count} keys deleted successfully.'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/quake/<quake_id>', methods=['GET'])
def get_quake(quake_id):
    """
    Retrieve earthquake data by quake_id from Redis.
    """
    try:
        data = rd.get(f"earthquake:{quake_id}")

        if data is None:
            return jsonify({'error': f'Earthquake ID {quake_id} not found.'}), 404

        quake_data = json.loads(data)

        return jsonify(quake_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """
    Get earthquake statistics within a given date range.

    Args:
        None.

    Query Parameters:
        start (str, optional): Start date in 'YYYY-MM-DD' format. If not provided, uses earliest record.
        endt (str, optional): End date in 'YYYY-MM-DD' format. If not provided, uses latest record.

    Returns:
        Response: A JSON response containing:
            - total_count (int)
            - max_magnitude (float or None)
            - min_magnitude (float or None)
            - max_depth (float or None)
            - min_depth (float or None)
            - magtype_counts (dict)
    """
    try:
        start_str = request.args.get('start')
        end_str = request.args.get('end')

        if start_str and end_str:
            start_ms, end_ms = parse_date_range(start_str, end_str)
        else:
            # fetch the earliest and latest scores from earthquakes:by_time in Redis
            first = rd.zrange('earthquakes:by_time', 0, 0, withscores=True)
            last = rd.zrevrange('earthquakes:by_time', 0, 0, withscores=True)

            if not first or not last:
                return jsonify({'message': 'No earthquake data available.'}), 200

            start_ms = int(first[0][1])
            end_ms = int(last[0][1])

        quake_ids = rd.zrangebyscore('earthquakes:by_time', start_ms, end_ms)

        if not quake_ids:
            return jsonify({'message': 'No earthquakes found in the given time range.'}), 200

        stats = calculate_stats(quake_ids)

        return jsonify({
            'total_count': len(quake_ids),
            'start_timestamp': start_ms,
            'end_timestamp': end_ms,
            **stats
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

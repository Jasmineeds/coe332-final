from flask import Flask, request, jsonify, send_file
import requests
import os
import json
from jobs import add_job, get_job_by_id
from redis_client import rd, jdb, res
from utils import parse_earthquake, parse_date_range, calculate_stats, parse_earthquakes_by_city, generate_magnitude_histogram_bytes
from geopy.distance import geodesic
from datetime import datetime, timedelta
from logger_config import get_logger
import uuid


logger = get_logger(__name__)

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

@app.route('/quakes', methods=['GET'])
def get_earthquake_ids():
    """
    Return a list of earthquake IDs stored in Redis.
    Optional query parameter `limit`.
    """
    try:
        ids = rd.smembers('earthquakes:ids')
        if not ids:
            logger.warning("No earthquake IDs found.")
            return jsonify({'message': 'No earthquake data available'}), 404

        earthquake_ids = list(ids)

        # get limit
        limit_param = request.args.get('limit')
        if limit_param is not None:
            try:
                limit = int(limit_param)
                if limit > 0:
                    earthquake_ids = earthquake_ids[:limit]
            except ValueError:
                return jsonify({'error': 'Invalid limit parameter'}), 400

        logger.info(f"Retrieved {len(earthquake_ids)} earthquake IDs.")
        return jsonify(earthquake_ids), 200

    except Exception as e:
        logger.exception("Failed to fetch earthquake IDs")
        return jsonify({'error': str(e)}), 500

@app.route('/quakes/<quake_id>', methods=['GET'])
def get_quake_data(quake_id):
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

@app.route('/city-histogram/<jobid>', methods=['POST'])
def create_city_earthquake_histogram(jobid):
    """
    Creates a histogram of earthquake magnitudes for a specified date range.
    """
    try:
        item = get_job_by_id(jobid)
        start_date = item['start_date']
        end_date = item['end_date']

        # Generate image bytes directly
        img_bytes = generate_magnitude_histogram_bytes(start_date, end_date)

        # Optional: Save to disk if needed
        output_dir = '/app/images'
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"histogram_{jobid}.png")
        with open(output_path, 'wb') as f:
            f.write(img_bytes)

        # Return image bytes in response (or use redirect/download URL)
        return Response(img_bytes, mimetype='image/png')

    except ValueError as e:
        return jsonify({"error": f"Date validation error: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Error generating histogram: {str(e)}"}), 500


@app.route('/jobs', methods=['POST'])
def submit_job():
    """
    Submit a new job by specifying start and end date.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    start_date = data.get('start_date')
    end_date = data.get('end_date')
    job_type = data.get('job_type', 'magnitude_distribution')

    if not start_date or not end_date:
        return jsonify({"error": "Please specify start_date and end_date."}), 400

    job = add_job(start_date, end_date, job_type)
    logger.info(f"New job submitted: {job['id']}")
    return jsonify(job), 202

@app.route('/jobs', methods=['GET'])
def list_jobs():
    """
    List all existing job IDs stored in Redis.
    """
    job_keys = jdb.keys()
    job_ids = [key.decode('utf-8') for key in job_keys]
    logger.info(f"Listed {len(job_ids)} jobs.")
    return jsonify(job_ids), 200

@app.route('/jobs/<jobid>', methods=['GET'])
def get_job(jobid: str):
    """
    Get job details by job_id.
    """
    job_data = jdb.get(jobid)
    if job_data is None:
        return jsonify({'error': f'Job {jobid} not found'}), 404
    try:
        job = json.loads(job_data)
        logger.info(f"Retrieved job data for job {jobid}.")
        return jsonify(job), 200
    except json.JSONDecodeError:
        return jsonify({'error': f'Invalid JSON format for job {jobid}'}), 500

@app.route('/results/<jobid>', methods=['GET'])
def get_results(jobid: str):
    """
    Retrieve the JSON result of a job.
    """
    if not res.exists(jobid):
        return jsonify({"error": f"Result for job {jobid} not found."}), 404

    raw_type = res.hget(jobid, 'type')
    result_type = raw_type.decode('utf-8')

    if result_type != 'json':
        return jsonify({"error": f"Job {jobid} is not a JSON result."}), 400

    raw_content = res.hget(jobid, 'content')
    try:
        data = json.loads(raw_content.decode('utf-8'))
        return jsonify(data), 200
    except json.JSONDecodeError:
        return jsonify({"error": "Stored JSON is invalid."}), 500

@app.route('/download/<jobid>', methods=['GET'])
def download_image(jobid: str):
    """
    Download the image result of a job.
    """
    if not res.exists(jobid):
        return jsonify({"error": f"Result for job {jobid} not found."}), 404

    raw_type = res.hget(jobid, 'type')
    result_type = raw_type.decode('utf-8')

    if result_type != 'image':
        return jsonify({"error": f"Job {jobid} is not an image result."}), 400

    content = res.hget(jobid, 'content')
    if content is None:
        return jsonify({"error": f"No image data for job {jobid}."}), 500

    # create images dir in container if not exit
    os.makedirs('/app/images', exist_ok=True)
    # temp file path
    path = f"/app/images/{jobid}.png"

    try:
        with open(path, 'wb') as f:
            f.write(content)
        return send_file(path, mimetype='image/png', as_attachment=True)
    
    except Exception as e:
        return jsonify({"error": f"Error writing image to file: {str(e)}"}), 500

#Help
@app.route('/help', methods=['GET'])
def help():
    """
    Returns a descriptions of the available routes in the API.
    """
    routes_info = {
        '/data': {
            'methods': ['POST', 'DELETE'],
            'description': 'Load earthquake data from a source and store it in Redis (POST), or delete all earthquake-related data from Redis (DELETE).'
        },
        '/quake/<quake_id>': {
            'methods': ['GET'],
            'description': 'Retrieve earthquake data by quake_id from Redis.'
        },
        '/stats': {
            'methods': ['GET'],
            'description': 'Get earthquake statistics within a given date range.'
        },
        '/jobs': {
            'methods': ['POST', 'GET'],
            'description': 'Submit a new job specifying start and end date (POST), or list all existing job IDs (GET).'
        },
        '/jobs/<jobid>': {
            'methods': ['GET'],
            'description': 'Get job details by job_id.'
        },
        '/results/<jobid>': {
            'methods': ['GET'],
            'description': 'Retrieve the JSON result of a job.'
        },
        '/download/<jobid>': {
            'methods': ['GET'],
            'description': 'Download the image result of a job.'
        }
    }

    return jsonify(routes_info), 200

@app.route('/closest-earthquake', methods=['GET'])
def closest_earthquake():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing JSON body"}), 400
        
        lat = float(data.get('lat'))
        lon = float(data.get('lon'))

        if not all([lat, lon]):
            return jsonify({"error": "Both latitude and longitude are required"}), 400
        
        # Query USGS API (limit to recent 1000 quakes)
        usgs_url = 'https://earthquake.usgs.gov/fdsnws/event/1/query'
        date_a_week_ago = datetime.now() - timedelta(days=7)
        iso_date_a_week_ago = date_a_week_ago.isoformat()
        
        params = {
            'format': 'geojson',
            'orderby': 'time',
            'limit': 1000,  # Adjust for performance
            'starttime': iso_date_a_week_ago,  # You can make this dynamic
        }

        response = requests.get(usgs_url, params=params)
        data = response.json()

        min_distance = float('inf')
        closest_quake = None

        for feature in data.get('features', []):
            quake_coords = feature['geometry']['coordinates']
            quake_latlon = (quake_coords[1], quake_coords[0])  # [lon, lat, depth]
            distance_km = geodesic((lat, lon), quake_latlon).kilometers

            if distance_km < min_distance:
                min_distance = distance_km
                closest_quake = feature

        if closest_quake:
            return jsonify({
                'distance_km': round(min_distance, 2),
                'location': closest_quake['properties']['place'],
                'magnitude': closest_quake['properties']['mag'],
                'time': closest_quake['properties']['time'],
                'url': closest_quake['properties']['url']
            })
        else:
            return jsonify({'error': 'No earthquake data found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    logger.info("Starting Flask app.")
    app.run(debug=True, host='0.0.0.0', port=5000)

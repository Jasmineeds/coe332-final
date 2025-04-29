# Tectonic Tantrums: The Exploration of Earthquakes

## Data Source

This project uses earthquake information from the United States Geological Survey (USGS) dataset, which provides authoritative and real-time data for global seismic activity. Get the dataset here:

[Search Earthquake Catalog](https://earthquake.usgs.gov/earthquakes/search/)

## Run Scripts

Use command in Makefile for dev.
```
make up        # Start and build containers
make down      # Stop and remove containers
make ps        # List container status
make reload    # load data into redis
make clear     # delete data in redis
```

## API Endpoints

- **POST `/data`**: Load and cache the full earthquake dataset into Redis.

**Command**

```curl -X POST http://localhost:5000/data```

**Response**
```json
{ "message": "Data loaded successfully: 11624 items stored." }
```
- **DELETE `/data`**: Delete the cached dataset from Redis.

**Command**

```curl -X DELETE http://localhost:5000/data```

**Response**
```json
{ "message": "11624 keys deleted successfully." }
```
- **GET `/quakes`**: Retrieve a list of all or partial earthquake IDs. Optional query parameter ```limit``` only return the first N entries.

**Command**

```curl -X GET http://localhost:5000/quakes?limit=3```

**Response**
```json
[
  "nc75143086",
  "av93547601",
  "uw62078791"
]
```
```json
{
  "error": "Invalid limit parameter"
}
```
- **GET `/quakes/<quake_id>`**: Retrieve a single earthquake data from Redis.

**Command**

```curl -X GET http://localhost:5000/quakes/ak0252t9tlwp```

**Response**
```json
{
  "id": "ak0252t9tlwp",
  "properties": {
    "alert": null,
    "cdi": null,
    "code": "0252t9tlwp",
    "detail": "https://earthquake.usgs.gov/fdsnws/event/1/query?eventid=ak0252t9tlwp&format=geojson",
    "dmin": null,
    "felt": null,
    "gap": null,
    "ids": ",ak0252t9tlwp,",
    "mag": 1.6,
    "magType": "ml",
    "...": "other properties are omitted for brevity"
  }
}
```
```json
{
  "error": "Earthquake ID ak0252t9tlwp not found."
}
```
- **GET `/stats`**: Returns aggregated statistics about earthquake events.

**Command**

```curl "http://localhost:5000/stats?start=2025-03-01&end=2025-03-02"```

**Response**
```json
{
  "start_timestamp": 1740787200000,
  "end_timestamp": 1740959999000,
  "max_depth": 616.344,
  "max_magnitude": 5.3,
  "min_depth": -3.18,
  "min_magnitude": -1.61,
  "magtype_counts": {
    "mb": 72,
    "md": 215,
    "ml": 494,
    "mwr": 1,
    "mww": 7
  },
  "total_count": 789
}
```
```json
{
  "message": "No earthquakes found in the given time range."
}
```
- **POST `/city-histogram`**: Creates a histogram of earthquake fequencies by city for a specified date range, through `start_date` and `end_date` parameters.

**Command**

```bash
curl -X POST \
  http://localhost:5000/city-histogram \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-02-27 00:00:00",
    "end_date": "2025-03-29 23:59:59"
  }'
```
Note: It is important that the backslash '\' is used to increase readability of the command, allowing a user to continue to the next line. Additionally, for the `start_date` and `end_date` parameters it is essential that the format is YYYY-MM-DD HH:MM:SS to avoid data validation errors.

**Response**
```json
{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "complete",
    "message": "Histogram generated successfully",
    "download_url": "/download/550e8400-e29b-41d4-a716-446655440000"
}
```
Note: This command writes the returned PNG image to `earthquakes_by_city_histogram.png` in your current directory, with a path determined by its unique job_id in downloads.
 
- **POST `/jobs`**: Create a new job. Add `start_date`, `end_date`, `job_type` in the parameters.

**Command**

```curl localhost:5000/jobs -X POST -d '{"start_date":"2025-03-01", "end_date":"2025-03-05", "job_type":"magnitude_distribution"}' -H "Content-Type: application/json"```

**Response**
```json
{
  "id": "1271512c-bdbd-4576-a62c-79dad40fb1b3",
  "start": "2025-03-01",
  "end": "2025-03-05",
  "type": "magnitude_distribution",
  "status": "submitted"
}
```
```json
{
  "error": "Please specify start_date and end_date."
}
```
- **GET `/jobs`**: List all the jobs in the queue.

**Command**

```curl localhost:5000/jobs```

**Response**
```json
[
  "71a40474-5ce8-48fe-bafa-c80da91d8e8d",
  "1271512c-bdbd-4576-a62c-79dad40fb1b3",
  "78d63cf4-35c6-4d0e-8953-f0d7f64fb3ea"
]
```
- **GET `/jobs/<jobid>`**: Get the information of a certain job.

**Command**

```curl localhost:5000/jobs/1271512c-bdbd-4576-a62c-79dad40fb1b3```

**Response**
```json
{
  "id": "1271512c-bdbd-4576-a62c-79dad40fb1b3",
  "start": "2025-03-01",
  "end": "2025-03-05",
  "type": "magnitude_distribution",
  "status": "in progress"
}
```
```json
{
  "error": "Job 1271512c-bdbd-4576-a62c-79dad40fb1 not found"
}
```
- **GET `/download/<jobid>`**: Download the result of a image job.

**Command**

```curl localhost:5000/download/e92ac09f-dbea-4aa8-a331-89f1fdbc7b42 --output earthquake_histogram.png```

**Response**
```
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100 26674  100 26674    0     0  4351k      0 --:--:-- --:--:-- --:--:-- 5209k
```

Note:
This command writes the returned PNG image to `earthquake_histogram.png` in your current directory. The service temporarily writes the image to `/app/images/<jobid>.png` before streaming.

## Testing

Integration tests and unit tests are located in the `test/` directory.

1. Run the containers
```
docker-compose up --build
```

2. Open a new terminal and navigate to the test directory
```
cd test
```

3. Run tests
```
pytest
```

4. See results
```
============================= test session starts ==============================
collected 12 items 

test_api.py ......
test_jobs.py .....  
test_worker.py .  

============================= 13 passed in 10.78s ===============================
```
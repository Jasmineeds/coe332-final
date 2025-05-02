# Tectonic Tantrums: The Exploration of Earthquakes

## Project Overview

Tectonic Tantrums is a project designed to explore and analyze earthquake data using information sourced from the United States Geological Survey (USGS). This application allows users to load, query, and visualize seismic activity through a robust API. The goal of this software is to foster a deeper understanding of earthquakes. Through the API endpoints, users can retrieve earthquake statistics, generate histograms of earthquake frequencies by city, and manage data efficiently. The project emphasizes user interaction and data management, providing a comprehensive tool for researchers, educators, and anyone interested in the dynamics of seismic events. With features such as job management for processing data and integration with Redis for efficient data caching, Tectonic Tantrums serves as a valuable resource for analyzing global seismic activity.

## Data Source

This project uses earthquake information from the United States Geological Survey (USGS) dataset, which provides authoritative and real-time data for global seismic activity. Get the dataset here:

[Search Earthquake Catalog](https://earthquake.usgs.gov/earthquakes/search/)

## Structure
```
tectonic-tantrums/
├── data
│   └── .gitcanary
├── img
│   ├── earthquake_histogram.png
│   └── diagram.png
├── docker-compose.yml
├── Dockerfile
├── kubernetes
│   ├── prod
│   │   ├── app-prod-deployment-flask.yml
│   │   ├── app-prod-deployment-redis.yml
│   │   ├── app-prod-deployment-worker.yml
│   │   ├── app-prod-ingress-flask.yml
│   │   ├── app-prod-pvc-redis.yml
│   │   ├── app-prod-service-flask.yml
│   │   ├── app-prod-service-nodeport-flask.yml
│   │   ├── app-prod-service-redis.yml
│   │   └── pvc-basic.yaml
│   └── test
│       ├── app-test-deployment-flask.yml
│       ├── app-test-deployment-redis.yml
│       ├── app-test-deployment-worker.yml
│       ├── app-test-ingress-flask.yml
│       ├── app-test-pvc-redis.yml
│       ├── app-test-service-flask.yml
│       ├── app-test-service-nodeport-flask.yml
│       ├── app-test-service-redis.yml
│       ├── pvc-basic.yaml
│       └── app-test-job.yml
├── Makefile
├── README.md
├── requirements.txt
├── src
│   ├── flask_api.py
│   ├── jobs.py
│   ├── worker.py
│   ├── utils.py
│   ├── logger_config.py
│   └── redis_clien.py
└── test
    ├── test_flask_api.py
    ├── test_jobs.py
    └── test_worker.py
```

## Getting Started 
First, clone the repository to your local machine:

```bash
git clone git@github.com:Jasmineeds/coe332-final.git
cd coe332-final
```

## Run Scripts
Use commands in Makefile for development.
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
Note: This command writes the returned PNG image to `earthquakes_by_city_histogram.png`, with a path determined by its unique job_id in downloads. To access the file you can use the `\downloads\<job_id>` route.
 


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



- **GET `/help`**: Returns a short description of possible endpoints that can be used

**Command**

```curl localhost:5000/help```

- **GET `/closest-earthquake`**: Returns information to do with the earthquake occuring closest to specified latitude and longitude values.

**Command**

```curl localhost:5000/closest-earthquake -X GET -d '{"lat":'30.2862175', "lon":'-97.739388'}' -H "Content-Type: application/json"```

**Response**
```
{
  "distance_km": 282.98,
  "location": "1 km ESE of Asherton, Texas",
  "magnitude": 2.3,
  "time": 1745926348890,
  "url": "https://earthquake.usgs.gov/earthquakes/eventpage/tx2025iimf"
}
```

## Testing

### Testing on Local Hardware (Jetstream)

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

### Testing on a Kubernetes Cluster (Test Env)

1. Deploy to the Kubernetes cluster
```
kubectl apply -f <deployment-file>.yaml
```
2. Run the tests
```
kubectl apply -f app-test-job.yml
```
3. Check the status of the job
```
kubectl get jobs
```
```
NAME       STATUS     COMPLETIONS   DURATION   AGE
test-job   Complete   1/1           19s        11m
```
4. View the logs for the test job
```
kubectl logs job/test-job
```
```
============================= test session starts ==============================
platform linux -- Python 3.9.22, pytest-7.4.4, pluggy-1.5.0
rootdir: /app
collected 12 items

tests/test_api.py ......                                                 [ 50%]
tests/test_jobs.py .....                                                 [ 91%]
tests/test_worker.py .                                                   [100%]

============================= 12 passed in 14.00s ==============================
```
5. Delete the test job
```
kubectl delete job test-job
```

## Software Diagram
![diagram](/img/diagram.png)

The diagram illustrates the architecture of the project:

### Redis

- `db=0`: Stores USGC data fetched from a third-party source
- `db=1`: Queue used by HotQueue for background job processing
- `db=2`: Job metadata database (jdb), storing submitted job details
- `db=3`: Stores job results (res) for retrieval

### Flask Application

- Hosts the API routes that handle user HTTP requests
- Includes job logic for creating, retrieving, and updating jobs in Redis

### Worker

- Continuously listens to the Redis queue
- Processes jobs and stores results in the result database

## AI Usage Disclaimer

Our team used AI to help us refine our test cases, use libraries such as geopy and debug errors on the command line. We learned that we could pass parameters with API calls to the USGS website in order to return more specific parts of the dataset. This helped us developed more complex routes such as the one that found the earthquake closest to the user. 

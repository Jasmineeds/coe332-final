# Tectonic Tantrums: The Exploration of Earthquakes

This is the final project for the COE 332 Software Engineering and Design, Spring 2025.

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
│   └── redis_client.py
└── test
    ├── test_flask_api.py
    ├── test_jobs.py
    └── test_worker.py
```

## Getting Started 

### Run on Local Hardware (Jetstream)

1. Clone the repository
```
git clone https://github.com/Jasmineeds/tectonic-tantrums.git
```

2. Navigate to the directory
```
cd tectonic-tantrums
```

3. Build the Containers
```
docker-compose up --build
```

Optional: Set environment log level in docker-compose.yml

```
environment:
  - LOG_LEVEL=WARNING
```

4. Check the docker containers
```
docker ps -a 
```

Make sure all three containers are up.
```
CONTAINER ID   IMAGE           COMMAND                  CREATED          STATUS          PORTS                                       NAMES
aea0146edbad   final_worker    "python3 worker.py"      10 seconds ago   Up 9 seconds    5000/tcp                                    final_worker_1
04f460f170b2   final_flask-api "python3 api.py"         10 seconds ago   Up 9 seconds    0.0.0.0:5000->5000/tcp, :::5000->5000/tcp   final_flask-api_1
557e4864aa9b   redis:7         "docker-entrypoint.s…"   10 seconds ago   Up 10 seconds   0.0.0.0:6379->6379/tcp, :::6379->6379/tcp   final_redis-db_1
```

The server will start in debug mode on ```https://localhost:5000```.

5. Shut down the containers
```
docker-compose down 
```

### Run on a Kubernetes Cluster

1. Clone the repository
```
git clone https://github.com/Jasmineeds/tectonic-tantrums.git
```

2. Navigate to the kubernetes directory
- For test environment
```
cd tectonic-tantrums/kubernetes/test
```
- For production environment
```
cd tectonic-tantrums/kubernetes/prod
```

3. Apply manifests
- For test environment
```
make apply-test
```
- For production environment
```
make apply-prod
```

or use `kubectl apply -f <yml-files>` to apply certain files.

4. Check resources

- Deployment
```bash
kubectl get deployment
```
Check if deployments are `AVAILABLE` and `READY`
```
NAME                        READY   UP-TO-DATE   AVAILABLE   AGE
flask-deployment-test       1/1     1            1           9h
redis-deployment-test       1/1     1            1           9h
test-pvc-redis-deployment   1/1     1            1           9h
worker-deployment-test      1/1     1            1           9h
```
- Pods
```bash
kubectl get pods
```
Check if pods are `Running`
```
NAME                                       READY   STATUS      RESTARTS   AGE
flask-deployment-test-59f89797bc-szjwl     1/1     Running     0          9h
redis-deployment-test-859b9cb995-c2hrr     1/1     Running     0          9h
test-pvc-redis-deployment-78967b54-zvzrr   1/1     Running     0          9h
worker-deployment-test-db75f9c7f-b7tbk     1/1     Running     0          9h
```
- PVC
```bash
kubectl get pvc
```
Check if persistent volume claims (PVC) status is `Bound`
```
NAME                         STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
redis-jasmineeds-data-test   Bound    pvc-1ff063ba-6316-4859-a0fe-b7b76ac00657   1Gi        RWO            cinder-csi     <unset>                 9h
```
- Service
```bash
kubectl get services
```
Check services and endpoints. Check the exposed port and try `curl coe332.tacc.cloud:31762/`
```
NAME                              TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
flask-api-nodeport-service-test   NodePort    10.233.62.152   <none>        5000:31762/TCP   9h
flask-api-service-test            ClusterIP   10.233.43.131   <none>        5000/TCP         9h
redis-service-test                ClusterIP   10.233.38.210   <none>        6379/TCP         9h
```
- Ingress
```bash
kubectl get ingress
```
Check ingress rules and host/path mappings
```
NAME                     CLASS   HOSTS                                      ADDRESS        PORTS   AGE
flask-api-ingress-test   nginx   test-tectonic-tantrums.coe332.tacc.cloud   10.233.1.210   80      9h
```

5. Access the application

Try to access to the `/help` route!

- For test environment
```bash
curl test-tectonic-tantrums.coe332.tacc.cloud/help
```
- For production environment
```bash
curl tectonic-tantrums.coe332.tacc.cloud/help
```

## Makefile
Use the Makefile for simplified commands.
```
# ====================
# Local Development
# ====================
make up           # Start and build containers
make down         # Stop and remove containers
make ps           # List container status
make reload       # load data into redis
make clear        # delete data in redis
# ====================
# Kubernetes deployment
# ====================
make apply-test   # Apply files to deploy the test env
make apply-prod   # Apply files to deploy the prod env
```

## API Endpoints

Replace `localhost:5000` with the Kubernetes ingress hostname when applicable. For example, `curl tectonic-tantrums.coe332.tacc.cloud/help`

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
This command writes the returned PNG image to `earthquake_histogram.png` in your current directory.

Output example:

![earthquake histogram](/img/earthquake_histogram.png)


- **GET `/closest-earthquake`**: Returns information to do with the earthquake occuring closest to specified latitude and longitude values.

**Command**

```curl localhost:5000/closest-earthquake -X GET -d '{"lat":'30.2862175', "lon":'-97.739388'}' -H "Content-Type: application/json"```

**Response**
```json
{
  "distance_km": 282.98,
  "location": "1 km ESE of Asherton, Texas",
  "magnitude": 2.3,
  "time": 1745926348890,
  "url": "https://earthquake.usgs.gov/earthquakes/eventpage/tx2025iimf"
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


- **GET `/help`**: Returns a short description of possible endpoints that can be used.

**Command**

```curl localhost:5000/help```

**Response**
```json
{
  "/data": {
    "description": "Load earthquake data from a source and store it in Redis (POST), or delete all earthquake-related data from Redis (DELETE).",
    "methods": [
      "POST",
      "DELETE"
    ]
  },
  "/download/<jobid>": {
    "description": "Download the image result of a job.",
    "methods": [
      "GET"
    ]
  },
  "/jobs": {
    "description": "Submit a new job specifying start and end date (POST), or list all existing job IDs (GET).",
    "methods": [
      "POST",
      "GET"
    ]
  },
  "...": "others are omitted for brevity"
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

============================= 12 passed in 10.78s ===============================
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

### Kubernetes

- **Deployment**: Manages application state, including replicas, resources, and container images.
- **Pod**: Represents a running instance of a process in the cluster, including one or more containers.
- **PVC (Persistent Volume Claim)**: Requests persistent storage for data retention even when Pods are deleted or restarted.
- **Service**: Exposes applications running on Pods for network communication with other services.
- **Ingress**: Controls external access to services, defining routing rules for traffic.

## AI Usage Disclaimer

Our team used AI to help us refine our test cases, use libraries such as geopy and debug errors on the command line. We learned that we could pass parameters with API calls to the USGS website in order to return more specific parts of the dataset. This helped us developed more complex routes such as the one that found the earthquake closest to the user. 

# Tectonic Tantrums: The Exploration of Earthquakes

## Data Source

This project uses earthquake information from the United States Geological Survey (USGS) dataset, which provides authoritative and real-time data for global seismic activity. Get the dataset here:

[Search Earthquake Catalog](https://earthquake.usgs.gov/earthquakes/search/)

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

- **GET `/quake/<quake_id>`**: Retrieve a single earthquake data from Redis.

**Command**

```curl -X GET http://localhost:5000/quake/ak0252t9tlwp```

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

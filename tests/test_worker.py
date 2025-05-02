import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import os
import sys

#gets related modules from src directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from utils import calculate_stats


MOCK_EARTHQUAKE_DATA = {
    "earthquake:1": json.dumps({
        "id": "1",
        "properties": {
            "mag": 1.7,
            "time": 1740959985586,
            "magType": "ml"
        },
        "geometry": {
            "coordinates": [-148.4734, 69.1513, 0.6]
        }
    }),
    "earthquake:2": json.dumps({
        "id": "2",
        "properties": {
            "mag": 3.2,
            "time": 1740959985000,
            "magType": "mb"
        },
        "geometry": {
            "coordinates": [-120.1234, 35.6789, 10.0]
        }
    }),
    "earthquake:3": json.dumps({
        "id": "3",
        "properties": {
            "mag": 2.0,
            "time": 1740959984000,
            "magType": "mb"
        },
        "geometry": {
            "coordinates": [100.0, -20.0, 5.0]
        }
    })
}

MOCK_JOB_ID = "test-job-id"
MOCK_JOB_DATA = {
        "id": MOCK_JOB_ID,
        "type": "magnitude_distribution",
        "start": "2025-03-01",
        "end": "2025-03-03",
}
MOCK_RESULTS_BYTES = b"mock_image_data"
MOCK_RESULTS_JSON = {"key":"value"}

@patch('utils.rd') #creates mock utils object for test
def test_calculate_stats(mock_rd):
    mock_rd.get.side_effect = lambda key: MOCK_EARTHQUAKE_DATA.get(key)

    result = calculate_stats(['1', '2', '3']) #test call

    #checks from mock data
    assert result['max_magnitude'] == 3.2
    assert result['min_magnitude'] == 1.7
    assert result['max_depth'] == 10.0
    assert result['min_depth'] == 0.6
    assert result['magtype_counts'] == {'ml': 1, 'mb': 2}

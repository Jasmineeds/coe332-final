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
MOCK_JOB_D = {
        "id": MOCK_JOB_ID,
        "type": "magnitude_distribution",
        "start": "2025-03-01",
        "end": "2025-03-03",
}
MOCK_RESULTS_BYTES = b"mock_image_data"
MOCK_RESULTS_JSON = {"key":"value"}

@patch('utils.rd')
def test_calculate_stats(mock_rd):
    mock_rd.get.side_effect = lambda key: MOCK_EARTHQUAKE_DATA.get(key)

    result = calculate_stats(['1', '2', '3'])

    assert result['max_magnitude'] == 3.2
    assert result['min_magnitude'] == 1.7
    assert result['max_depth'] == 10.0
    assert result['min_depth'] == 0.6
    assert result['magtype_counts'] == {'ml': 1, 'mb': 2}

@patch("worker.get_job_by_id") #creates mock objects for test
@patch("worker.update_job_status")
@patch("worker.res")
def test_do_work_success_image(mock_res, mock_update_job_status, mock_get_job_by_id): #test do_work for a job that successfully creates an image
    #mocks
    mock_get_job_by_id.return_value = MOCK_JOB_DATA 
    JOB_HANDLERS["magnitude_distribution"] = MagicMock(return_value=MOCK_RESULTS_BYTES)

    #worker function
    do_work(MOCK_JOB_ID)

    #checks/assertions
    mock_update_job_status.assert_any_call(MOCK_JOB_ID, "in progress")
    mock_update_job_status.assert_any_call(MOCK_JOB_ID, "complete")
    JOB_HANDLERS["magnitude_distribution"].assert_called_once_with(
        MOCK_JOB_DATA["start"], MOCK_JOB_DATA["end"]
    )
    mock_res.hset.assert_called_once_with(
        MOCK_JOB_ID,
        mapping={
            "type": "image",
            "content": MOCK_RESULTS_BYTES,
        },
    )

@patch("worker.get_job_by_id") #creates mocks
@patch("worker.update_job_status")
@patch("worker.res")
def test_do_work_success_json(mock_res, mock_update_job_status, mock_get_job_by_id): #tests for job with a successful JSON response
    #mocks
    mock_get_job_by_id.return_value = MOCK_JOB_DATA
    JOB_HANDLERS["magnitude_distribution"] = MagicMock(return_value=MOCK_RESULTS_JSON)

    #worker
    do_work(MOCK_JOB_ID)

    #checks
    mock_update_job_status.assert_any_call(MOCK_JOB_ID, "in progress")
    mock_update_job_status.assert_any_call(MOCK_JOB_ID, "complete")
    JOB_HANDLERS["magnitude_distribution"].assert_called_once_with(
        MOCK_JOB_DATA["start"], MOCK_JOB_DATA["end"]
    )
    mock_res.hset.assert_called_once_with(
        MOCK_JOB_ID,
        mapping={
            "type": "json",
            "content": '{"key": "value"}',
        },
    )

@patch("worker.get_job_by_id") #mocks for test
@patch("worker.update_job_status")
def test_do_work_missing_job_data(mock_update_job_status, mock_get_job_by_id): #tests do_work w/no job data
    #mock the job data to None
    mock_get_job_by_id.return_value = None

    #worker function
    do_work(MOCK_JOB_ID)

    #checks response
    mock_update_job_status.assert_any_call(MOCK_JOB_ID, "in progress")
    mock_update_job_status.assert_any_call(MOCK_JOB_ID, "failed")

@patch("worker.get_job_by_id") #mocks
@patch("worker.update_job_status")
def test_do_work_unsupported_job_type(mock_update_job_status, mock_get_job_by_id): #tests w/unsupported job_type
    # mock w/ bad job type
    mock_get_job_by_id.return_value = {
        "id": MOCK_JOB_ID,
        "type": "unsupported_job_type",
        "start": "2025-03-01",
        "end": "2025-03-03",
    }

    #worker function
    do_work(MOCK_JOB_ID)

    #checks/assertions
    mock_update_job_status.assert_any_call(MOCK_JOB_ID, "in progress")
    mock_update_job_status.assert_any_call(MOCK_JOB_ID, "failed")

@patch("worker.get_job_by_id") #mocks for test
@patch("worker.update_job_status")
def test_do_work_missing_dates(mock_update_job_status, mock_get_job_by_id): #missing start and end inputs from user
    #mock job data w/ missing dates
    mock_get_job_by_id.return_value = {
        "id": MOCK_JOB_ID,
        "type": "magnitude_distribution",
        "start": None,
        "end": None,
    }

    #worker function
    do_work(MOCK_JOB_ID)

    #checks
    mock_update_job_status.assert_any_call(MOCK_JOB_ID, "in progress")
    mock_update_job_status.assert_any_call(MOCK_JOB_ID, "failed")

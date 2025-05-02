import pytest
import json
from unittest.mock import patch, MagicMock
import sys
import os
#get related jobs files/functionalities from src directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from jobs import _generate_jid, _instantiate_job, add_job, get_job_by_id, update_job_status

TEST_JOB_DATA = {
    "id": "abc-123",
    "status": "submitted",
    "start": "2025-03-01",
    "end": "2025-03-03",
    "type": "test_job_type"
}

def test_generate_jid(): #tests job_id is the correct length/format
    jid = _generate_jid()
    assert isinstance(jid, str)
    assert len(jid) == 36  # length of UUID4 format

def test_instantiate_job(): #tests the validity of job creation
    jid = "abc-123"
    job = _instantiate_job(jid, "submitted", "2025-03-01", "2025-03-03", "test_job_type")
    assert job == TEST_JOB_DATA

#tests that jobs are being added to the queue and redis db
@patch('jobs.q') #patch creates mock objects for test
@patch('jobs.jdb')
def test_add_job(mock_jdb, mock_q): # patch decorator affect db order
    mock_jdb.set = MagicMock()
    mock_q.put = MagicMock()

    job = add_job("2025-03-01", "2025-03-03", "test_job_type")
    assert job["start"] == "2025-03-01"
    assert job["status"] == "submitted"
    # assert db called once
    mock_jdb.set.assert_called_once()
    mock_q.put.assert_called_once()

@patch('jobs.jdb') #mock object for test
def test_get_job_by_id(mock_jdb): #tests that a user can get the correct info for a specific job id
    mock_jdb.get.return_value = json.dumps(TEST_JOB_DATA)
    
    job = get_job_by_id("abc-123")
    assert job["id"] == "abc-123"

@patch('jobs.jdb') #mock object for test
def test_update_job_status(mock_jdb): #tests that accurate job statuses are being given
    mock_jdb.get.return_value = json.dumps(TEST_JOB_DATA)
    mock_jdb.set = MagicMock()

    update_job_status("abc-123", "complete")
    updated = json.loads(mock_jdb.set.call_args[0][1])
    assert updated["status"] == "complete"

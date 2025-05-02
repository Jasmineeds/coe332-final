import requests
import time
import re
import pytest

api_host = 'localhost'
api_port = '5000'
api_prefix = f'http://{api_host}:{api_port}'

def test_load_data():
    response = requests.post(f"{api_prefix}/data")
    assert response.status_code == 200
    assert "message" in response.json()

def get_first_quake_id():
    response = requests.get(f"{api_prefix}/quakes")
    if response.status_code == 404:
        pytest.skip("No quake data available")
    assert response.status_code == 200
    ids = response.json()
    if not ids:
        pytest.skip("Quake list is empty")
    return ids[0]

def test_get_quake_ids():
    response = requests.get(f"{api_prefix}/quakes")
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        assert isinstance(response.json(), list)

def test_get_gene_data():
    quake_id = get_first_quake_id()
    response = requests.get(f"{api_prefix}/quakes/{quake_id}")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
    assert response.json().get('id') == quake_id

def submit_test_job():
    payload = {
        "start_date": "2025-03-01",
        "end_date": "2025-03-02"
    }
    response = requests.post(f"{api_prefix}/jobs", json=payload)
    assert response.status_code == 202
    job = response.json()
    assert "id" in job
    return job["id"]

def test_submit_job():
    jid = submit_test_job()
    assert isinstance(jid, str)

def test_get_job():
    jid = submit_test_job()
    time.sleep(1)  # wait for worker
    response = requests.get(f"{api_prefix}/jobs/{jid}")
    assert response.status_code == 200
    job = response.json()
    assert job["id"] == jid
    assert job["status"] in ["submitted", "in progress", "complete", "failed"]

def test_help_info():
    response = requests.get(f"{api_prefix}/help")
    assert response.ok
    assert response.status_code == 200
    assert bool(re.search('Submit a new job', response.text))

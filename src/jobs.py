import json
import uuid
from typing import Dict, Optional
from redis_client import q, jdb

from logger_config import get_logger

logger = get_logger(__name__)

def _generate_jid() -> str:
    """
    Generate a pseudo-random identifier for a job.

    Returns:
        jid (str): A random job ID.
    """
    jid = str(uuid.uuid4())
    logger.debug(f"Generated job ID: {jid}")
    return jid

def _instantiate_job(jid: str, status: str, start: str, end: str) -> Dict[str, str]:
    """
    Create the job object description as a python dictionary. Requires the job id,
    status, start and end parameters.
    
    Parameters:
        jid (str): unique identifier for the job
        status (str): current status of the job
        start (str): user-provided parameter
        end (str): user-provided parameter

    Returns:
        dict: Job metadata dictionary.
    """
    job_dict = {
        "id": jid,
        "status": status,
        "start": start,
        "end": end
    }
    logger.debug(f"Instantiated job: {job_dict}")
    return job_dict

def _save_job(jid: str, job_dict: Dict[str, str]) -> None:
    """
    Save a job object in the Redis database.

    Args:
        jid (str): Job ID.
        job_dict (dict): Job metadata dictionary.
    """
    jdb.set(jid, json.dumps(job_dict))
    logger.info(f"Saved job {jid} to Redis.")

def _queue_job(jid: str) -> None:
    """
    Add a job to the Redis queue.

    Args:
        jid (str): Job ID.
    """
    q.put(jid)
    logger.info(f"Queued job {jid}.")

def add_job(start: str, end: str, status: str = "submitted") -> Dict[str, str]:
    """
    Add a new job: generate an ID, create job metadata, store it, queue it.

    Args:
        start (str): Start date.
        end (str): End date.
        status (str): Job status (default: 'submitted').

    Returns:
        job_dict (dict): Job metadata dict.
    """
    jid = _generate_jid()
    job_dict = _instantiate_job(jid, status, start, end)
    _save_job(jid, job_dict)
    _queue_job(jid)
    logger.info(f"Added new job {jid}.")
    return job_dict

def get_job_by_id(jid: str) -> Optional[Dict[str, str]]:
    """
    Return job dictionary given a job ID.

    Args:
        jid (str): Job ID.

    Returns:
        dict or None: Job dict if found, else None.
    """
    raw = jdb.get(jid)
    if raw:
        logger.debug(f"Retrieved job {jid}.")
        return json.loads(raw)
    logger.warning(f"Job ID {jid} not found.")
    return None

def update_job_status(jid: str, status: str) -> None:
    """
    Update the status of a job.

    Args:
        jid (str): Job ID.
        status (str): New status string.
    """
    job_dict = get_job_by_id(jid)
    if job_dict:
        job_dict['status'] = status
        _save_job(jid, job_dict)
        logger.info(f"Updated job {jid} status to '{status}'")
    else:
        logger.error(f"Job ID {jid} not found.")
        raise Exception(f"Job ID {jid} not found.")
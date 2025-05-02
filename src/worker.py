import time
import json
from jobs import get_job_by_id, update_job_status
from utils import generate_magnitude_histogram_bytes, generate_city_quake_histogram_bytes
from redis_client import q, res
from logger_config import get_logger

logger = get_logger(__name__)

JOB_HANDLERS = {
    'magnitude_distribution': generate_magnitude_histogram_bytes,
    'earthquake_count_by_city': generate_city_quake_histogram_bytes
}

@q.worker
def do_work(jid: str) -> None:
    logger.info(f"Processing job: {jid}")
    update_job_status(jid, 'in progress')

    try:
        job_data = get_job_by_id(jid)
        if not job_data:
            raise ValueError(f"No job data found for jid: {jid}")

        job_type = job_data.get('type')
        start_date = job_data.get('start')
        end_date = job_data.get('end')

        logger.info(f"Job {jid} type: {job_type}")

        if not start_date or not end_date:
            raise ValueError("Missing start or end date") 

        handler = JOB_HANDLERS.get(job_type)
        if not handler:
            raise ValueError(f"Unsupported job type: {job_type}")

        results = handler(start_date, end_date)
        logger.info(f"Results type for job {jid}: {type(results)}")

        # storage depends on result type
        if isinstance(results, dict):
            res.hset(jid, mapping={
                'type': 'json',
                'content': json.dumps(results),
            })
        elif isinstance(results, bytes):
            res.hset(jid, mapping={
                'type': 'image',
                'content': results,
            })
        else:
            raise ValueError(f"Unsupported result type for job {jid}.")

        update_job_status(jid, 'complete')
        logger.info(f"Job {jid} completed.")

    except Exception as e:
        logger.exception(f"Job {jid} failed: {e}")
        update_job_status(jid, 'failed')

if __name__ == "__main__":
    logger.info("Worker is listening for jobs...")
    do_work()

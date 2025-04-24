import time
from jobs import get_job_by_id, update_job_status
from redis_client import q
from logger_config import get_logger

logger = get_logger(__name__)

@q.worker
def do_work(jid: str) -> None:
    logger.info(f"Processing job: {jid}")
    update_job_status(jid, 'in progress')
    time.sleep(10)   # there is no real work for now
    update_job_status(jid, 'complete')

if __name__ == "__main__":
    logger.info("Worker is listening for jobs...")
    do_work()

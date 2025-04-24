# src/redis_client.py
import os
import redis
from hotqueue import HotQueue

_redis_ip = os.environ.get('REDIS_HOST', 'redis-db')
_redis_port = int(os.environ.get("REDIS_PORT", 6379))

rd = redis.Redis(host=_redis_ip, port=_redis_port, db=0, decode_responses=True)
q = HotQueue("queue", host=_redis_ip, port=_redis_port, db=1)
jdb = redis.Redis(host=_redis_ip, port=_redis_port, db=2)
res = redis.Redis(host=_redis_ip, port=_redis_port, db=3)

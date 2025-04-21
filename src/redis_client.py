# src/redis_client.py
import redis

_redis_ip='127.0.0.1'
_redis_port=6379

rd = redis.Redis(host=_redis_ip, port=_redis_port, db=0, decode_responses=True)

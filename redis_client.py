import redis
from typing import Iterator

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True,
)

def get_redis() -> Iterator[redis.Redis]:
    yield redis_client
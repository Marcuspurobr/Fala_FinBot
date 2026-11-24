"""Conexão com o Redis. Um único cliente é criado e reaproveitado."""
from functools import lru_cache

import redis

from .config import require_redis_url


@lru_cache(maxsize=1)
def get_redis() -> redis.Redis:
    # decode_responses: as respostas chegam como texto, não como bytes
    return redis.Redis.from_url(require_redis_url(), decode_responses=True)

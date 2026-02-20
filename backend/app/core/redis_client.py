"""Cliente Redis para cache de PDF por hash."""
import logging
from typing import Optional

from redis import Redis

from app.config import settings

logger = logging.getLogger(__name__)

_redis: Optional[Redis] = None

CACHE_KEY_PREFIX = "pdf:hash:"
CACHE_TTL_SECONDS = 86400 * 30  # 30 dias


def get_redis() -> Optional[Redis]:
    """Obtiene el cliente Redis. Retorna None si Redis no esta disponible."""
    global _redis
    if _redis is not None:
        return _redis
    try:
        _redis = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
        )
        _redis.ping()
        logger.info("Redis conectado: %s", settings.redis_url)
        return _redis
    except Exception as e:
        logger.warning("Redis no disponible: %s. Cache deshabilitado.", e)
        _redis = None
        return None


def get_cached_source_file_id(file_hash: str) -> Optional[int]:
    """
    Busca en Redis si el hash ya fue procesado.
    Retorna source_file_id si existe, None si no.
    """
    r = get_redis()
    if not r:
        return None
    try:
        key = f"{CACHE_KEY_PREFIX}{file_hash}"
        val = r.get(key)
        if val is not None:
            return int(val)
    except Exception as e:
        logger.warning("Error leyendo cache Redis: %s", e)
    return None


def set_cached_source_file_id(file_hash: str, source_file_id: int) -> None:
    """Guarda en Redis el mapeo hash -> source_file_id."""
    r = get_redis()
    if not r:
        return
    try:
        key = f"{CACHE_KEY_PREFIX}{file_hash}"
        r.setex(key, CACHE_TTL_SECONDS, str(source_file_id))
    except Exception as e:
        logger.warning("Error escribiendo cache Redis: %s", e)

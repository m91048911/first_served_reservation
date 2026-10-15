import json
import redis

from fastapi import APIRouter, Depends
from redis_client import get_redis

router = APIRouter(prefix="/events", tags=["Events"])

# 실제 db조회
def get_event_from_db(event_id: int):
    return {
        "id": event_id,
        "name": f"공연 {event_id}",
        "venue": "서울"
    }

@router.get("/{event_id}")
def get_event(
    event_id: int,
    r: redis.Redis = Depends(get_redis)
):
    key = f"event:{event_id}"
    # redis 조회
    cached = r.get(key)
    # 있으면 캐시 리턴
    if cached is not None:
        return {
            "source": "cached",
            "event": json.loads(cached)
        }
    
    # 캐시가 없으면 db에서 조회
    event = get_event_from_db(event_id)
    # 조회 후 redis에 저장 TTL 60초
    r.set(key, json.dumps(event), ex=60)
    
    return {
        "source": "database",
        "event": event
    }

@router.put("/{event_id}")
def update_event(
    event_id: int,
    r: redis.Redis = Depends(get_redis)
):
    updated_event = {
        "id": event_id,
        "name": "new event",
        "venue": "new venue"
    }
    # 캐시 삭제
    r.delete(f"event:{event_id}")

    return {
        "message": "정보 수정, 캐시 삭제",
        "event": updated_event
    }
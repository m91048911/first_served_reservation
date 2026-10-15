import uuid
import redis
from fastapi import APIRouter, Depends
from redis_client import get_redis

router = APIRouter(prefix="/seats", tags=["Seats"])

# 검증하고 삭제하는 lua스크립트
RELEASE_LOCK_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
else
    return 0
end
"""

# 락의 시간 갱신 스크립트
RENEW_LOCK_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('expire', KEYS[1], ARGV[2])
else
    return 0
end
"""

@router.post("/{seat_id}/reserve/{user_id}")
def reserve_seat(
    seat_id: str,
    user_id: str,
    r: redis.Redis = Depends(get_redis)
):
    key = f"seat:{seat_id}"
    lock_token = str(uuid.uuid4())

    success = r.set(
        key,
        lock_token,
        nx=True,
        ex=600
    )
    if not success:
        return {"success": False, "message": "이미 선점된 좌석입니다"}
    
    return {
        "success": True,
        "message": "좌석 선점 성공",
        "seat_id": seat_id,
        "user_id": user_id,
        "lock_token": lock_token
    }

@router.delete("/{seat_id}/lock")
def release_seat_lock(
    seat_id: str,
    lock_token: str,
    r: redis.Redis = Depends(get_redis)
):
    key = f"seat:{seat_id}"

    result = r.eval(
        RELEASE_LOCK_SCRIPT,
        1,
        key,
        lock_token
    )

    if result == 1:
        return {
            "success": True,
            "message": "락 해제 성공"
        }

    return {
        "success": False,
        "message": "락이 없거나 락 소유자가 아닙니다"
    }

@router.post("/{seat_id}/renew")
def lock_seat_renew(
    seat_id: str,
    lock_token: str,
    r: redis.Redis = Depends(get_redis)
):
    key = f"seat:{seat_id}"
    result = r.eval(
        RENEW_LOCK_SCRIPT,
        1,
        key,
        lock_token,
        600
    )
    if result == 1:
        return {
            "success": True,
            "message": "락 갱신 성공"
        }

    return {
        "success": False,
        "message": "락이 없거나 락 소유자가 아닙니다"
    }
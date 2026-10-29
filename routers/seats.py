import uuid
import redis

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from redis_client import get_redis
from database import get_db
from models.reservation import Reservation

router = APIRouter(prefix="/seats", tags=["Seats"])

# 락 소유자를 검증한 뒤 삭제
RELEASE_LOCK_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
else
    return 0
end
"""

# 락 소유자를 검증한 뒤 TTL 갱신
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
    r: redis.Redis = Depends(get_redis),
    db: Session = Depends(get_db)
):
    key = f"seat:{seat_id}"
    lock_token = str(uuid.uuid4())

    # 1. Redis에서 좌석 선점
    success = r.set(
        key,
        lock_token,
        nx=True,
        ex=600
    )
    if not success:
        return {
            "success": False,
            "message": "이미 선점된 좌석입니다"
        }

    # 2. Redis 선점 성공 후 DB에 예약 기록 저장
    try:
        reservation = Reservation(
            seat_id=seat_id,
            user_id=user_id,
            status="pending"
        )

        db.add(reservation)
        db.commit()
        db.refresh(reservation)
        
        return {
            "success": True,
            "message": "좌석 선점 및 예약 기록 저장 성공",
            "reservation_id": reservation.id,
            "seat_id": seat_id,
            "user_id": user_id,
            "status": reservation.status,
            "lock_token": lock_token
        }
    except SQLAlchemyError:
        db.rollback()

        # 3. DB 저장 실패 시, 내 토큰이 일치할 때만 락 해제
        r.eval(
            RELEASE_LOCK_SCRIPT,
            1,
            key,
            lock_token
        )

        return {
            "success": False,
            "message": "예약 정보 저장에 실패했습니다"
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
import pytest
import fakeredis
import uuid

from fastapi.testclient import TestClient
from main import app
from redis_client import get_redis
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

# 테스용 redis
@pytest.fixture
def fake_redis():
    return fakeredis.FakeRedis(decode_responses=True)

# 시작전 후 redis의 데이터 삭제
# @pytest.fixture
# def clean_seat():
#     key = f"seat:A-10"
#     fake_redis.delete(key)

#     yield

#     fake_redis.delete(key)
#     app.dependency_overrides.clear()



@pytest.fixture
def client(fake_redis):
    # 기존클라이언트 대체
    def override_get_redis():
        yield fake_redis
    
    # get_redis 대체
    app.dependency_overrides[get_redis] = override_get_redis

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_redis, None)


# 테스트 함수
# 좌석예약
def test_seat_reservation(client, fake_redis):
    # clean_seat에서 fakeredis로 변경
    fake_redis.delete("seat:A-10")

    first = client.post("/seats/A-10/reserve/user1")
    assert first.status_code == 200
    assert first.json()["success"] is True

    second = client.post("/seats/A-10/reserve/user2")
    assert second.status_code == 200
    assert second.json()["success"] is False


# lock 삭제
def test_release_seat_lock(client):
    # 첫번째 사람 선점
    first = client.post("/seats/A-10/reserve/user1")
    assert first.status_code == 200
    assert first.json()["success"] is True
    
    lock_token = first.json()["lock_token"]

    # 락토큰으로 삭제되는지
    response = client.delete(
        "/seats/A-10/lock",
        params={"lock_token": lock_token},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

    # 다음사람 선점여부
    second = client.post("/seats/A-10/reserve/user2")
    assert second.status_code == 200
    assert second.json()["success"] is True


# lock 갱신
def test_lock_seat_renew(client):

    first = client.post("/seats/A-10/reserve/user1")
    assert first.status_code == 200
    assert first.json()["success"] is True
    
    lock_token = first.json()["lock_token"]

    response = client.post("/seats/A-10/renew", params={"lock_token": lock_token})
    assert response.status_code == 200
    assert response.json()["success"] is True

    second = client.post("/seats/A-10/reserve/user2")
    assert second.status_code == 200
    assert second.json()["success"] is False

# 잘못된 락으로 삭제시도하고 삭제되었는지 확인
def test_release_with_wrong_token(client, fake_redis):
    first = client.post("/seats/A-10/reserve/user1")
    assert first.status_code == 200
    assert first.json()["success"] is True
    lock_token = first.json()["lock_token"]
    
    wrong_token = str(uuid.uuid4())

    response = client.delete(
        "/seats/A-10/lock",
        params={"lock_token": wrong_token},
    )
    assert response.status_code == 200
    assert response.json()["success"] is False

    assert fake_redis.get("seat:A-10") == lock_token

    second = client.post("/seats/A-10/reserve/user2")
    assert second.status_code == 200
    assert second.json()["success"] is False


def test_concurrent_seat_reservation(client, fake_redis):
    fake_redis.delete("seat:A-10")

    # 유저10명 준비
    user_ids = [f"user{i}" for i in range(10)]
    barrier = Barrier(10)

    def reserve(user_id):
        barrier.wait()
        return client.post(
            f"/seats/A-10/reserve/{user_id}"
        )

    # 최대 10개의 스레드
    with ThreadPoolExecutor(max_workers=10) as executor:
        responses = list(executor.map(reserve, user_ids))

    success_count = sum(
        response.json()["success"]
        for response in responses
    )

    assert success_count == 1

    failure_count = sum(
        not response.json()["success"]
        for response in responses
    )

    assert failure_count == 9
    assert fake_redis.get("seat:A-10") is not None
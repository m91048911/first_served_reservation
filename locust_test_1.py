from locust import HttpUser, task, between, events
import redis

fail_cnt = 0
success_cnt = 0

r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True,
)

class SeatReservationUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def reserve_seat(self):
        global fail_cnt, success_cnt
        with self.client.post(
            "/seats/A-10/reserve/user1",
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"HTTP 오류: {response.status_code}"
                )
                return

            try:
                data = response.json()
            except ValueError:
                response.failure("잘못된 JSON 응답")
                return

            if data.get("success") is True:
                response.success()
                success_cnt += 1
            elif data.get("message") == "이미 선점된 좌석입니다":
                response.success()
                fail_cnt += 1
            else:
                response.failure("예상하지 못한 API 응답")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    global fail_cnt, success_cnt

    print(f"선점 성공 횟수: {success_cnt}")
    print(f"선점 거절 횟수: {fail_cnt}")
    print(f"전체 선점 요청 횟수: {success_cnt + fail_cnt}")
    
    # 데이터 초기화
    deleted = r.delete("seat:A-10")
    print(f"Redis 키 삭제: {'성공' if deleted == 1 else '이미 없음'}")
    fail_cnt = 0
    success_cnt = 0
    r.close()
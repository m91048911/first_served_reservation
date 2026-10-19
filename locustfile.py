
import uuid
from locust import HttpUser, task, between, events

fail_cnt = 0
success_cnt = 0

class SeatReservationUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def reserve_seat(self):
        global fail_cnt, success_cnt
        seat_id = f"TEST-{uuid.uuid4()}"
        with self.client.post(
            f"/seats/{seat_id}/reserve/user1",
            catch_response=True,
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
    print(f"선점 성공 횟수: {success_cnt}")
    print(f"선점 거절 횟수: {fail_cnt}")
    print(f"전체 선점 요청 횟수: {success_cnt + fail_cnt}")

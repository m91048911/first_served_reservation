from locust import HttpUser, task, between, events
import random
from threading import Lock

success_cnt = 0
reject_cnt = 0
error_cnt = 0

counter_lock = Lock()

class SeatReservationUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def reserve_seat(self):
        global success_cnt, reject_cnt, error_cnt

        # 미리 정해진 1,000개 좌석 중 하나 선택
        seat_id = f"LOAD-{random.randint(1, 1000)}"

        with self.client.post(
            f"/seats/{seat_id}/reserve/user1",
            catch_response=True,
        ) as response:

            if response.status_code != 200:
                response.failure(
                    f"HTTP 오류: {response.status_code}"
                )
                with counter_lock:
                    error_cnt += 1
                return

            try:
                data = response.json()
            except ValueError:
                response.failure("잘못된 JSON 응답")
                with counter_lock:
                    error_cnt += 1
                return

            with counter_lock:
                if data.get("success") is True:
                    success_cnt += 1
                    response.success()

                elif data.get("message") == "이미 선점된 좌석입니다":
                    reject_cnt += 1
                    response.success()

                else:
                    error_cnt += 1
                    response.failure("예상하지 못한 API 응답")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    total = success_cnt + reject_cnt + error_cnt

    print(f"선점 성공: {success_cnt}")
    print(f"선점 거절: {reject_cnt}")
    print(f"오류: {error_cnt}")
    print(f"전체 요청: {total}")

    if total:
        print(f"성공률: {success_cnt / total * 100:.2f}%")
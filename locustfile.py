
from locust import HttpUser, task, between


class SeatReservationUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def reserve_seat(self):
        with self.client.post(
            "/seats/A-10/reserve/user1",
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
            elif data.get("message") == "이미 선점된 좌석입니다":
                response.success()
            else:
                response.failure("예상하지 못한 API 응답")


from locust import HttpUser, task, constant
import uuid


class SeatReservationUser(HttpUser):
    wait_time = constant(0)

    @task
    def reserve_seat(self):
        user_id = str(uuid.uuid4())

        with self.client.post(
            f"/seats/A-10/reserve/{user_id}",
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
                response.failure("JSON 응답 오류")
                return

            if data.get("success") is True:
                response.success()
            else:
                response.failure("이미 선점된 좌석")

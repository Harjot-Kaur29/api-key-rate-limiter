from locust import HttpUser, task, between
import json
from pathlib import Path


USERS_FILE = Path(__file__).parent / "load_test_users.json"

with open(USERS_FILE, "r") as file:
    USERS = json.load(file)


class RateLimiterUser(HttpUser):

    wait_time = between(1, 2)

    user_index = 0

    def on_start(self):

        self.user_data = USERS[
            RateLimiterUser.user_index % len(USERS)
        ]

        RateLimiterUser.user_index += 1

        self.token = self.user_data["token"]
        self.api_key = self.user_data["api_key"]

        print(
            f"Started: {self.user_data['username']}"
        )

    @task
    def test_demo(self):

        with self.client.get(
            "/demo",
            headers={
                "X-API-Key": self.api_key
            },
            catch_response=True
        ) as response:

            if response.status_code == 200:
                response.success()

            elif response.status_code == 429:
                response.success()

            else:
                response.failure(
                    f"Unexpected status: {response.status_code}"
                )
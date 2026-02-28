from locust import HttpUser, task, between
import random
import string

class RateLimitUser(HttpUser):
    wait_time = between(0.01, 0.05)  # aggressive — 20-100 req/sec per user

    def on_start(self):
        # Each simulated user gets a random API key
        self.api_key = "".join(random.choices(string.ascii_lowercase, k=8))

    @task(3)
    def hit_api_hello(self):
        self.client.get(
            "/api/hello",
            headers={"X-API-Key": self.api_key},
            name="/api/hello"
        )

    @task(1)
    def hit_api_data(self):
        self.client.get(
            "/api/data",
            headers={"X-API-Key": self.api_key},
            name="/api/data"
        )

    @task(1)
    def hit_health(self):
        self.client.get("/health", name="/health")

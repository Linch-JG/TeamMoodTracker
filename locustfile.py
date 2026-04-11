"""Locust smoke test for the Team Mood Tracker API."""

from __future__ import annotations

from uuid import uuid4

from locust import HttpUser, between, events, task


P95_RESPONSE_TIME_THRESHOLD_MS = 150


class MoodTrackerUser(HttpUser):
    """Synthetic user for basic API load and latency checks."""

    wait_time = between(0.2, 0.8)

    @task(3)
    def submit_mood(self) -> None:
        """Exercise the primary write path under light load."""

        payload = {
            "user": f"load-test-{uuid4().hex[:8]}",
            "mood": "neutral",
            "rating": 3,
            "comment": "Locust performance smoke test.",
        }
        with self.client.post(
            "/mood-entries",
            json=payload,
            name="/mood-entries",
            catch_response=True,
        ) as response:
            if response.status_code != 201:
                response.failure(f"Unexpected status code: {response.status_code}")

    @task(1)
    def healthcheck(self) -> None:
        """Exercise the smoke endpoint used by CI and local automation."""

        with self.client.get(
            "/health",
            name="/health",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Unexpected status code: {response.status_code}")


@events.quitting.add_listener
def evaluate_thresholds(environment, **_kwargs) -> None:
    """Fail the load test when latency or reliability regress beyond the agreed threshold."""

    stats = environment.stats.total
    p95_latency_ms = stats.get_response_time_percentile(0.95)
    has_failures = stats.fail_ratio > 0
    if has_failures or p95_latency_ms > P95_RESPONSE_TIME_THRESHOLD_MS:
        environment.process_exit_code = 1
        return

    environment.process_exit_code = 0

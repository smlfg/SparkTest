"""
Locust load testing configuration for Agent 7.

Test scenarios:
- 10 users, 10 minutes
- 20 users, 5 minutes
- Spike to 50 users

Run with:
    locust -f tests/load/locustfile.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between, events
import json
import time
import random


class Agent7User(HttpUser):
    """Simulated Agent 7 user performing various tasks."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """Called when a user starts."""
        self.login()

    def login(self):
        """Login to the system."""
        response = self.client.post("/api/auth/login", json={
            "username": f"user_{random.randint(1, 100)}",
            "password": "test_password"
        })

        if response.status_code == 200:
            self.token = response.json().get("token", "")
        else:
            self.token = ""

    @task(3)
    def check_system_status(self):
        """Check system status (frequent operation)."""
        headers = {"Authorization": f"Bearer {self.token}"}
        with self.client.get(
            "/api/system/status",
            headers=headers,
            catch_response=True,
            name="Check System Status"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(2)
    def list_models(self):
        """List available models."""
        headers = {"Authorization": f"Bearer {self.token}"}
        with self.client.get(
            "/api/models",
            headers=headers,
            catch_response=True,
            name="List Models"
        ) as response:
            if response.status_code == 200:
                models = response.json().get("models", [])
                response.success()
            else:
                response.failure(f"Failed to list models")

    @task(1)
    def upload_dataset(self):
        """Upload a dataset."""
        headers = {"Authorization": f"Bearer {self.token}"}

        # Simulate dataset upload
        dataset = [
            {
                "instruction": f"Question {i}",
                "input": "",
                "output": f"Answer {i}"
            }
            for i in range(10)
        ]

        files = {
            "file": ("dataset.json", json.dumps(dataset), "application/json")
        }

        with self.client.post(
            "/api/datasets/upload",
            headers=headers,
            files=files,
            catch_response=True,
            name="Upload Dataset"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Upload failed: {response.status_code}")

    @task(1)
    def start_training(self):
        """Start a training job."""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        training_config = {
            "model_name": "unsloth/llama-3-8b-bnb-4bit",
            "dataset_id": f"dataset_{random.randint(1, 100)}",
            "lora_r": 8,
            "num_epochs": 1,
            "learning_rate": 2e-4
        }

        with self.client.post(
            "/api/train/start",
            headers=headers,
            json=training_config,
            catch_response=True,
            name="Start Training"
        ) as response:
            if response.status_code in [200, 201]:
                job_id = response.json().get("job_id")
                response.success()
                # Store job_id for status checks
                if not hasattr(self, "training_jobs"):
                    self.training_jobs = []
                self.training_jobs.append(job_id)
            else:
                response.failure(f"Training start failed: {response.status_code}")

    @task(2)
    def check_training_status(self):
        """Check training job status."""
        if not hasattr(self, "training_jobs") or not self.training_jobs:
            return

        job_id = random.choice(self.training_jobs)
        headers = {"Authorization": f"Bearer {self.token}"}

        with self.client.get(
            f"/api/train/status/{job_id}",
            headers=headers,
            catch_response=True,
            name="Check Training Status"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status check failed")

    @task(2)
    def run_inference(self):
        """Run model inference."""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        inference_request = {
            "model": "default_model",
            "prompt": f"Test prompt {random.randint(1, 1000)}",
            "max_tokens": 100
        }

        with self.client.post(
            "/api/inference",
            headers=headers,
            json=inference_request,
            catch_response=True,
            name="Run Inference"
        ) as response:
            if response.status_code == 200:
                latency = response.json().get("latency_ms", 0)
                if latency < 2000:  # 2 second SLA
                    response.success()
                else:
                    response.failure(f"Inference too slow: {latency}ms")
            else:
                response.failure(f"Inference failed: {response.status_code}")

    @task(1)
    def check_gpu_status(self):
        """Check GPU availability."""
        headers = {"Authorization": f"Bearer {self.token}"}

        with self.client.get(
            "/api/system/gpu",
            headers=headers,
            catch_response=True,
            name="Check GPU Status"
        ) as response:
            if response.status_code == 200:
                gpu_info = response.json()
                if gpu_info.get("available"):
                    response.success()
                else:
                    response.failure("GPU not available")
            else:
                response.failure(f"GPU check failed")


class StudentWorkflowUser(HttpUser):
    """User simulating complete student workflow."""

    wait_time = between(2, 5)

    def on_start(self):
        """Initialize student session."""
        self.token = None
        self.dataset_id = None
        self.job_id = None
        self.login()

    def login(self):
        """Student login."""
        response = self.client.post("/api/auth/login", json={
            "username": f"student_{random.randint(1, 50)}",
            "password": "student_pass"
        })
        if response.status_code == 200:
            self.token = response.json().get("token")

    @task
    def complete_workflow(self):
        """Execute complete student workflow."""
        if not self.token:
            self.login()
            return

        headers = {"Authorization": f"Bearer {self.token}"}

        # Step 1: Check system
        self.client.get("/api/system/status", headers=headers, name="1. Check System")

        # Step 2: Check GPU
        self.client.get("/api/system/gpu", headers=headers, name="2. Check GPU")

        # Step 3: Upload dataset
        dataset = [{"instruction": "Q", "input": "", "output": "A"}] * 5
        files = {"file": ("data.json", json.dumps(dataset), "application/json")}
        upload_resp = self.client.post(
            "/api/datasets/upload",
            headers=headers,
            files=files,
            name="3. Upload Dataset"
        )

        if upload_resp.status_code == 200:
            self.dataset_id = upload_resp.json().get("dataset_id")

            # Step 4: Start training
            train_resp = self.client.post(
                "/api/train/start",
                headers=headers,
                json={
                    "dataset_id": self.dataset_id,
                    "model_name": "test_model",
                    "epochs": 1
                },
                name="4. Start Training"
            )

            if train_resp.status_code in [200, 201]:
                self.job_id = train_resp.json().get("job_id")

                # Step 5: Monitor training
                time.sleep(1)
                self.client.get(
                    f"/api/train/status/{self.job_id}",
                    headers=headers,
                    name="5. Check Training"
                )

                # Step 6: Test inference (assuming training completes quickly)
                self.client.post(
                    "/api/inference",
                    headers=headers,
                    json={"model": "test_model", "prompt": "Test"},
                    name="6. Test Inference"
                )


# Custom load shapes for different scenarios

from locust import LoadTestShape


class SteadyLoad10Users(LoadTestShape):
    """10 users for 10 minutes."""

    def tick(self):
        run_time = self.get_run_time()

        if run_time < 600:  # 10 minutes
            return (10, 1)  # 10 users, 1 user/sec spawn rate

        return None


class SteadyLoad20Users(LoadTestShape):
    """20 users for 5 minutes."""

    def tick(self):
        run_time = self.get_run_time()

        if run_time < 300:  # 5 minutes
            return (20, 2)  # 20 users, 2 users/sec spawn rate

        return None


class SpikeLoad(LoadTestShape):
    """Spike to 50 users."""

    def tick(self):
        run_time = self.get_run_time()

        if run_time < 60:
            # Start with 10 users
            return (10, 1)
        elif run_time < 120:
            # Spike to 50 users
            return (50, 10)
        elif run_time < 300:
            # Back to 20 users
            return (20, 2)
        else:
            return None


class StepLoad(LoadTestShape):
    """Step load increase."""

    def tick(self):
        run_time = self.get_run_time()

        if run_time < 60:
            return (5, 1)
        elif run_time < 120:
            return (10, 1)
        elif run_time < 180:
            return (15, 1)
        elif run_time < 240:
            return (20, 2)
        elif run_time < 300:
            return (25, 2)
        else:
            return None


# Event listeners for custom metrics

@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Track request metrics."""
    if exception:
        print(f"Request failed: {name} - {exception}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    print("=" * 60)
    print("Load Test Starting")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops."""
    print("=" * 60)
    print("Load Test Complete")
    print("=" * 60)

    # Print summary stats
    stats = environment.stats
    print(f"\nTotal requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")


if __name__ == "__main__":
    import os
    os.system("locust -f tests/load/locustfile.py")

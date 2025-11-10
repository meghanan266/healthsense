from locust import HttpUser, task, between, events
import json
import time

class HealthSenseAPIUser(HttpUser):
    # """
    # Simulates a dashboard user making API calls
    # """
    # wait_time = between(2, 5)  # Wait 2-5 seconds between tasks
    
    def on_start(self):
        """Called when a user starts"""
        self.tenant_id = "acme-clinic"
        self.device_ids = [f"watch-{i:04d}" for i in range(10)]  # 10 devices
    
    @task(3)  # Weight: 3x more likely than other tasks
    def get_all_devices(self):
        """Get all devices - most common dashboard action"""
        with self.client.get(
            "/api/v1/devices",
            params={"tenant_id": self.tenant_id},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("count", 0) > 0:
                    response.success()
                else:
                    response.failure("No devices returned")
            else:
                response.failure(f"Got status {response.status_code}")
    
    @task(1)  # Weight: 1x
    def get_device_latest(self):
        """Get latest data for a specific device"""
        device_id = self.device_ids[int(time.time()) % len(self.device_ids)]
        with self.client.get(
            f"/api/v1/devices/{device_id}/latest",
            params={"tenant_id": self.tenant_id},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Device not found is acceptable
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")
    
    @task(1)
    def get_timeseries(self):
        """Get timeseries data (placeholder endpoint)"""
        device_id = self.device_ids[0]
        with self.client.get(
            f"/api/v1/devices/{device_id}/timeseries",
            params={
                "tenant_id": self.tenant_id,
                "from": "2025-01-01T00:00:00Z",
                "to": "2025-12-31T23:59:59Z"
            },
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")
    
    @task(2)
    def health_check(self):
        """Health check endpoint"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    response.success()
                else:
                    response.failure("Unhealthy status")
            else:
                response.failure(f"Got status {response.status_code}")


# Custom metrics collection
response_times = []

@events.request.add_listener
def record_response_time(request_type, name, response_time, response_length, exception, **kwargs):
    """Record response times for later analysis"""
    if exception is None:
        response_times.append({
            'endpoint': name,
            'response_time': response_time,
            'timestamp': time.time()
        })

@events.quitting.add_listener
def save_results(environment, **kwargs):
    """Save results when test completes"""
    if response_times:
        import csv
        with open('../../docs/locust-results.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['endpoint', 'response_time', 'timestamp'])
            writer.writeheader()
            writer.writerows(response_times)
        print(f"\n✅ Saved {len(response_times)} response times to docs/locust-results.csv")
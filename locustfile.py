# Locust Load Testing Script — Task 97
# Run with: locust -f locustfile.py --host=http://localhost:8000

from locust import HttpUser, task, between


class TozalashAPIUser(HttpUser):
    wait_time = between(0.5, 2)

    @task(5)
    def health_check(self):
        self.client.get("/health")

    @task(3)
    def get_inventory(self):
        self.client.get("/api/v1/inventory/warehouse", headers=self._auth_headers())

    @task(2)
    def get_heatmap(self):
        self.client.get("/api/v1/intelligence/heatmap/orders")

    @task(2)
    def get_cross_sell(self):
        self.client.get("/api/v1/intelligence/recommendations/user_123")

    @task(1)
    def list_tickets(self):
        self.client.get("/api/v1/telegram/helpdesk/tickets")

    def _auth_headers(self) -> dict:
        return {"Authorization": "Bearer test_token"}

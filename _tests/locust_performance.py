"""
Grafana Performance Tests
=======================

Locust load tests for Grafana API endpoints with distributed support
"""
import logging
import os

from locust import HttpUser, between, events, task
from locust.runners import MasterRunner, WorkerRunner

from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment settings
ENV = os.getenv("ENVIRONMENT", "staging")
MASTER_HOST = os.getenv("LOCUST_MASTER_HOST", "localhost")
MASTER_PORT = os.getenv("LOCUST_MASTER_PORT", "5557")

class GrafanaUser(HttpUser):
    """Simulates user load against Grafana API"""
    host = settings.GRAFANA_URL
    wait_time = between(1, 3)
    
    def on_start(self):
        """Setup test headers"""
        self.headers = {
            "Authorization": f"Bearer {settings.GRAFANA_API_KEY}",
            "Content-Type": "application/json",
            "X-Test-Environment": ENV
        }

    @task(3)
    def view_dashboard(self):
        with self.client.get(
            "/api/dashboards/uid/fastapi", 
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed with {response.status_code}")
                logger.error(f"Dashboard view failed: {response.text}")

    @task(1)
    def list_alerts(self):
        with self.client.get(
            "/api/alerts", 
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed with {response.status_code}")
                logger.error(f"Alert list failed: {response.text}")

# Distributed test setup
@events.init.add_listener
def on_locust_init(environment, **kwargs):
    if isinstance(environment.runner, WorkerRunner):
        logger.info(f"Connected to master at {MASTER_HOST}:{MASTER_PORT}")
    elif isinstance(environment.runner, MasterRunner):
        logger.info("Running as master node")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    logger.info(f"Starting distributed test for {ENV} environment")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    logger.info(f"Test completed for {ENV} environment")

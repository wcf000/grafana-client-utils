# conftest.py
import os
import subprocess
import time
from prometheus_client import CollectorRegistry
from unittest.mock import MagicMock

import pytest
import requests
import traceback

from app.core.grafana.client import GrafanaClient


# Mock all Redis-related imports
def mock_redis_dependencies(monkeypatch):
    monkeypatch.setattr("app.core.redis.config.RedisConfig", MagicMock())
    monkeypatch.setattr("app.core.redis.client.RedisClient", MagicMock())
    monkeypatch.setattr("app.core.redis.rate_limit", MagicMock())



# --- Grafana Docker Compose Test Infra (session scoped, DRY, robust) ---

# * Always check both localhost and 127.0.0.1 for Grafana health to support Windows, WSL, and CI reliably
GRAFANA_HEALTH_URLS = [
    "http://localhost:3000/api/health",
    "http://127.0.0.1:3000/api/health"
]
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
COMPOSE_FILE = os.path.join(BACKEND_DIR, "app", "core", "grafana", "docker", "docker-compose.grafana.yml")
CHECK_INTERVAL = 3  # seconds
MAX_WAIT = 60  # seconds


def is_grafana_healthy():
    for url in GRAFANA_HEALTH_URLS:
        try:
            print(f"[GRAFANA HEALTHCHECK] Checking: {url}", flush=True)
            resp = requests.get(url, timeout=2)
            print(f"[GRAFANA HEALTHCHECK] Status: {resp.status_code}, Body: {resp.text}", flush=True)
            try:
                data = resp.json()
                print(f"[GRAFANA HEALTHCHECK] JSON: {data}", flush=True)
            except Exception as e:
                print(f"[GRAFANA HEALTHCHECK] Failed to parse JSON: {e}", flush=True)
            if resp.status_code == 200:
                print(f"[GRAFANA HEALTHCHECK] Healthy at: {url} (status 200)", flush=True)
                return True
        except Exception as e:
            print(f"[GRAFANA HEALTHCHECK] Exception for {url}: {e}", flush=True)
            traceback.print_exc()
    return False

@pytest.fixture(scope="session", autouse=True)
def grafana_docker():
    try:
        print(f"[GRAFANA DOCKER] Starting Grafana for tests...", flush=True)
        subprocess.run(
            ["docker", "compose", "-f", COMPOSE_FILE, "up", "-d"],
            cwd=BACKEND_DIR,
            check=True
        )
        waited = 0
        while not is_grafana_healthy() and waited < MAX_WAIT:
            print(f"[GRAFANA HEALTHCHECK] Waiting for Grafana to become healthy... ({waited}/{MAX_WAIT}s)", flush=True)
            time.sleep(CHECK_INTERVAL)
            waited += CHECK_INTERVAL
        if not is_grafana_healthy():
            print(f"[GRAFANA HEALTHCHECK] Grafana did not become healthy after {MAX_WAIT}s. Skipping tests.", flush=True)
            print("[GRAFANA HEALTHCHECK] Pausing for 30 seconds for manual inspection...", flush=True)
            import time
            time.sleep(30)
            subprocess.run(
                ["docker", "compose", "-f", COMPOSE_FILE, "down", "--remove-orphans"],
                cwd=BACKEND_DIR
            )
            pytest.skip("Grafana did not become healthy in time.")
        else:
            print("[GRAFANA HEALTHCHECK] Grafana is healthy!", flush=True)
        yield
    finally:
        print(f"[GRAFANA DOCKER] Tearing down Grafana after tests...", flush=True)
        subprocess.run(
            ["docker", "compose", "-f", COMPOSE_FILE, "down", "--remove-orphans"],
            cwd=BACKEND_DIR
        )


@pytest.fixture(autouse=True)
def isolated_prometheus_registry(monkeypatch):
    """
    Use a fresh CollectorRegistry for each test session to avoid metric duplication.
    """
    from app.core.grafana._tests import metrics as metrics_mod
    test_registry = CollectorRegistry()
    API_RESPONSE_TIME, TEST_SUCCESS, TEST_FAILURE = metrics_mod.get_metrics(registry=test_registry)
    monkeypatch.setattr(metrics_mod, "API_RESPONSE_TIME", API_RESPONSE_TIME)
    monkeypatch.setattr(metrics_mod, "TEST_SUCCESS", TEST_SUCCESS)
    monkeypatch.setattr(metrics_mod, "TEST_FAILURE", TEST_FAILURE)
    yield

# Mock settings
class TestSettings:
    GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")
    GRAFANA_API_KEY = os.getenv("GRAFANA_API_KEY", "test_key")
    # ! Set correct docker-compose and Dockerfile locations
    DOCKER_COMPOSE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../docker/docker-compose.grafana.yml"))
    DOCKERFILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../docker/DockerFile"))


def wait_for_grafana_ready(url: str, timeout: int = 60) -> bool:
    """
    Wait for Grafana to be healthy by polling the /login endpoint.
    Returns True if healthy within timeout, else False.
    """
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(f"{url}/login", timeout=3)
            if resp.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False

@pytest.fixture(scope="session", autouse=True)
def grafana_docker(request):
    """
    Start Grafana via docker-compose before tests, wait for healthy, tear down after.
    Skips tests if Grafana fails to start.
    """
    compose_file = TestSettings.DOCKER_COMPOSE_PATH
    env = os.environ.copy()
    # ! Optionally set env vars for Grafana admin user/pass/port here
    up_cmd = ["docker-compose", "-f", compose_file, "up", "-d"]
    down_cmd = ["docker-compose", "-f", compose_file, "down"]
    try:
        subprocess.run(up_cmd, check=True, env=env)
    except Exception as e:
        pytest.skip(f"Could not start Grafana via docker-compose: {e}")
        return
    healthy = wait_for_grafana_ready(TestSettings.GRAFANA_URL)
    if not healthy:
        subprocess.run(down_cmd, env=env)
        pytest.skip("Grafana did not become healthy in time.")
        return
    yield
    subprocess.run(down_cmd, env=env)

@pytest.fixture(scope="session")
def grafana_client():
    return GrafanaClient(
        url=TestSettings.GRAFANA_URL, credential=TestSettings.GRAFANA_API_KEY
    )

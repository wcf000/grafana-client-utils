# conftest.py
import os
from unittest.mock import MagicMock

import pytest

from app.core.grafana.client import GrafanaClient


# Mock all Redis-related imports
def mock_redis_dependencies(monkeypatch):
    monkeypatch.setattr("app.core.redis.config.RedisConfig", MagicMock())
    monkeypatch.setattr("app.core.redis.client.RedisClient", MagicMock())
    monkeypatch.setattr("app.core.redis.rate_limit", MagicMock())

@pytest.fixture(autouse=True)
def auto_mock_redis_dependencies(monkeypatch):
    mock_redis_dependencies(monkeypatch)

# Mock settings
class TestSettings:
    GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")
    GRAFANA_API_KEY = os.getenv("GRAFANA_API_KEY", "test_key")


@pytest.fixture(scope="session")
def grafana_client():
    return GrafanaClient(
        url=TestSettings.GRAFANA_URL, credential=TestSettings.GRAFANA_API_KEY
    )

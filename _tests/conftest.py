# _tests/conftest.py
import os

import pytest
from grafana_client import GrafanaApi


@pytest.fixture(scope="session")
def grafana_client():
    """Shared Grafana client fixture for all tests"""
    return GrafanaApi.from_url(
        url=os.getenv("GRAFANA_URL", "http://localhost:3000"),
        credential=os.getenv("GRAFANA_API_KEY", ""),
    )


@pytest.fixture(autouse=True)
def setup_metrics(monkeypatch):
    """Auto-configure metrics for all tests"""
    monkeypatch.setenv("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus")

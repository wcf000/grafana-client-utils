# _tests/conftest.py
import pytest
from grafana_client import GrafanaApi

from app.core.config import settings


@pytest.fixture(scope="session")
def grafana_client():
    """Shared Grafana client fixture for all tests"""
    return GrafanaApi.from_url(
        url=settings.GRAFANA_URL, credential=settings.GRAFANA_API_KEY
    )


@pytest.fixture(autouse=True)
def setup_metrics(monkeypatch):
    """Auto-configure metrics for all tests"""
    monkeypatch.setenv("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus")


@pytest.fixture(scope="session", autouse=True)
def cleanup_after_tests(grafana_client):
    """Clean up test data after all tests run"""
    yield
    
    # Clean up test dashboards
    dashboards = grafana_client.search.search_dashboards(tag="test")
    for db in dashboards:
        grafana_client.dashboard.delete_dashboard(db["uid"])
        
    # Clean up test alert channels
    channels = grafana_client.alerting.get_notification_channels()
    for channel in [c for c in channels if c.get("name", "").startswith("test-")]:
        grafana_client.alerting.delete_notification_channel(channel["id"])

# alert_test.py
from grafana_client import GrafanaApi


def test_alert_notification_channels(grafana_client):
    """Verify critical alert channels are configured"""
    channels = grafana_client.alerting.get_notification_channels()
    assert any(channel["type"] == "email" for channel in channels)
    assert any(channel["type"] == "slack" for channel in channels)

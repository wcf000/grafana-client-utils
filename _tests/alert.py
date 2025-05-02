# alert_test.py
from grafana_client import GrafanaApi


def test_alert_notification_channels(grafana_client):
    """Verify critical alert channels are configured"""
    try:
        channels = grafana_client.alerting.get_notification_channels()
        assert any(channel["type"] == "email" for channel in channels)
        assert any(channel["type"] == "slack" for channel in channels)
    finally:
        # Clean up any test channels created
        test_channels = [c for c in grafana_client.alerting.get_notification_channels() 
                        if c.get("name", "").startswith("test-")]
        for channel in test_channels:
            grafana_client.alerting.delete_notification_channel(channel["id"])

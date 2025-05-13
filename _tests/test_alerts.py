import asyncio
from datetime import datetime
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from app.core.grafana.alert_manager import (
    AlertRule,
    GrafanaAlertManager,
    GrafanaError,
    GrafanaTimeoutError,
)
import os

from app.core.grafana.client import GrafanaClient

from app.core.grafana.models import TimeoutThresholds


@pytest.fixture
def mock_grafana_client():
    client = MagicMock(spec=GrafanaClient)
    client.get_client.return_value = MagicMock()
    client.get_async_client.return_value = MagicMock()
    return client


@pytest.fixture
def alert_manager(mock_grafana_client):
    return GrafanaAlertManager(
        client=mock_grafana_client,
        timeout=TimeoutThresholds(create_alert=10)
    )


@pytest.fixture
def sample_alert():
    return AlertRule(
        uid="test-alert",
        title="Test Alert",
        condition="avg() > 10",
        severity="critical"
    )


def test_create_alert_success(alert_manager, sample_alert, isolated_prometheus_registry, mock_grafana_client):
    API_RESPONSE_TIME, TEST_SUCCESS, TEST_FAILURE = isolated_prometheus_registry
    """Test successful alert creation"""
    mock_client = mock_grafana_client.get_client.return_value
    mock_client.alerting.create_alert_rule.return_value = {
        "uid": sample_alert.uid,
        "title": sample_alert.title
    }

    result = alert_manager.create_alert(sample_alert)
    assert result["uid"] == sample_alert.uid
    mock_client.alerting.create_alert_rule.assert_called_once_with(sample_alert.dict())


def test_create_alert_validation_error(alert_manager):
    """Test alert validation"""
    with pytest.raises(ValueError):
        AlertRule(
            uid="",  # Invalid empty uid
            title="Test",
            condition="avg() > 10",
            severity="critical"
        )


@patch("app.core.grafana.alert_manager.ALERT_OPERATIONS.labels")
def test_create_alert_failure(mock_metrics, alert_manager, sample_alert, mock_grafana_client):
    """Test alert creation failure"""
    mock_client = mock_grafana_client.get_client.return_value
    mock_client.alerting.create_alert_rule.side_effect = Exception("API Error")

    with pytest.raises(GrafanaError):
        alert_manager.create_alert(sample_alert)

    mock_metrics.assert_called_with("create", "error")


@pytest.mark.asyncio
async def test_async_create_alert_success(alert_manager, sample_alert, mock_grafana_client):
    """Test async alert creation"""
    mock_client = mock_grafana_client.get_async_client.return_value
    mock_client.alerting.async_create_alert_rule = AsyncMock(return_value={
        "uid": sample_alert.uid
    })

    result = await alert_manager.async_create_alert(sample_alert)
    assert result["uid"] == sample_alert.uid


@pytest.mark.asyncio
async def test_async_create_alert_timeout(alert_manager, sample_alert, mock_grafana_client):
    """Test async alert creation timeout"""
    mock_client = mock_grafana_client.get_async_client.return_value
    mock_client.alerting.async_create_alert_rule.side_effect = asyncio.TimeoutError()

    with pytest.raises(GrafanaTimeoutError):
        await alert_manager.async_create_alert(sample_alert)


def test_bulk_create_alerts(alert_manager, sample_alert, mock_grafana_client):
    """Test bulk alert creation"""
    alerts = [sample_alert, sample_alert.model_copy(update={"uid": "alert-2"})]
    mock_client = mock_grafana_client.get_client.return_value
    mock_client.alerting.create_alert_rule.return_value = {"uid": "test"}

    results = alert_manager.bulk_create_alerts(alerts)
    assert len(results["success"]) == 2
    assert not results["failed"]


def test_validate_alert_response(alert_manager):
    """Test response validation"""
    valid_response = {"uid": "test", "title": "Test", "condition": "avg() > 10"}
    assert alert_manager._validate_alert_response(valid_response)

    with pytest.raises(ValueError):
        alert_manager._validate_alert_response({"uid": "test"})  # Missing fields


def test_alert_version_management(alert_manager, sample_alert):
    """Test version tracking"""
    with patch.object(alert_manager, "get_alert_version", return_value=1):
        version = alert_manager.update_alert_version("test", 2, "user1")
        assert version.version == 2
        assert version.updated_by == "user1"

    with pytest.raises(ValueError):
        alert_manager.update_alert_version("test", 1, "user1")  # Version must increment

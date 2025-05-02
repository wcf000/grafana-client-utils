"""
Production-ready Grafana alert management with:
- Retry logic with exponential backoff
- Async support
- Prometheus metrics
- Timeout handling
- Alert validation
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from circuitbreaker import circuit
from prometheus_client import Counter, Histogram
from pydantic import BaseModel, Field, validator
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.grafana.client import GrafanaClient
from app.core.grafana.exceptions import (
    ErrorDetail,
    GrafanaError,
    GrafanaRateLimitError,
    GrafanaTimeoutError,
)
from app.core.grafana.models import TimeoutThresholds

# Metrics
ALERT_OPERATIONS = Counter(
    "grafana_alert_operations_total", "Total alert operations", ["operation", "status"]
)
ALERT_LATENCY = Histogram(
    "grafana_alert_operations_latency_seconds", "Alert operation latency", ["operation"]
)

logger = logging.getLogger("grafana.alerts")


class AlertRule(BaseModel):
    """Production-ready Grafana alert rule model"""

    uid: str = Field(..., min_length=1, max_length=40)
    title: str = Field(..., min_length=1, max_length=255)
    condition: str
    severity: str = Field(..., regex=r"^(critical|warning|info)$")
    enabled: bool = True
    annotations: Dict[str, str] = {}
    labels: Dict[str, str] = {}

    @validator("condition")
    def validate_condition(cls, v):
        if not v.strip():
            raise ValueError("Condition cannot be empty")
        return v


class AlertRuleVersion(BaseModel):
    """Track alert rule versions for change management"""

    version: int = Field(1, ge=1)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: str


class GrafanaAlertManager:
    def __init__(
        self,
        client: GrafanaClient,
        timeout: Optional[TimeoutThresholds] = None,
    ):
        """Initialize with production-ready configuration"""
        self.client = client
        self.timeout = timeout or TimeoutThresholds()

    @circuit(failure_threshold=5, recovery_timeout=60, name="grafana_alerts")
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=(GrafanaRateLimitError, GrafanaTimeoutError),
    )
    @ALERT_LATENCY.time()
    def create_alert(self, alert: AlertRule) -> Dict[str, Any]:
        """Create a new alert rule with production hardening"""
        try:
            grafana = self.client.get_client()
            result = grafana.alerting.create_alert_rule(alert.dict())

            ALERT_OPERATIONS.labels("create", "success").inc()
            logger.info(f"Created alert {alert.uid}")
            return result

        except Exception as e:
            ALERT_OPERATIONS.labels("create", "error").inc()
            error = GrafanaError(
                ErrorDetail(
                    code="alert_create_error",
                    message=f"Failed to create alert: {str(e)}",
                    context={"alert_uid": alert.uid},
                )
            )
            error.log_error()
            raise error

    @circuit(failure_threshold=5, recovery_timeout=60, name="grafana_alerts_bulk")
    def bulk_create_alerts(self, alerts: List[AlertRule]) -> Dict[str, Any]:
        """Batch create alerts with circuit breaker protection"""
        results = {"success": [], "failed": []}

        for alert in alerts:
            try:
                result = self.create_alert(alert)
                results["success"].append({"uid": alert.uid, "version": 1})
            except Exception as e:
                results["failed"].append({"uid": alert.uid, "error": str(e)})

        return results

    @circuit(failure_threshold=5, recovery_timeout=60, name="grafana_alerts_async")
    async def async_create_alert(self, alert: AlertRule) -> Dict[str, Any]:
        """Async version with timeout handling"""
        try:
            async with asyncio.timeout(self.timeout.for_operation("create_alert")):
                grafana = await self.client.get_async_client()
                result = await grafana.alerting.async_create_alert_rule(alert.dict())

                ALERT_OPERATIONS.labels("create", "success").inc()
                logger.info(f"Async created alert {alert.uid}")
                return result

        except asyncio.TimeoutError:
            ALERT_OPERATIONS.labels("create", "timeout").inc()
            raise GrafanaTimeoutError(
                operation="async_create_alert",
                timeout=self.timeout.for_operation("create_alert"),
                threshold=self.timeout,
            )
        except Exception as e:
            ALERT_OPERATIONS.labels("create", "error").inc()
            error = GrafanaError(
                ErrorDetail(
                    code="async_alert_create_error",
                    message=f"Async alert creation failed: {str(e)}",
                    context={"alert_uid": alert.uid},
                )
            )
            error.log_error()
            raise error

    @circuit(failure_threshold=5, recovery_timeout=60, name="grafana_alerts_bulk_async")
    async def async_bulk_create_alerts(self, alerts: List[AlertRule]) -> Dict[str, Any]:
        """Async batch create with circuit breaker"""
        results = {"success": [], "failed": []}

        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(self._safe_async_create(alert)) for alert in alerts]

        for task in tasks:
            if task.exception():
                results["failed"].append(
                    {"uid": task.get_name(), "error": str(task.exception())}
                )
            else:
                results["success"].append(task.result())

        return results

    async def _safe_async_create(self, alert: AlertRule) -> Dict[str, Any]:
        """Wrapper for async create with error handling"""
        try:
            return await self.async_create_alert(alert)
        except Exception as e:
            logger.error(f"Async alert creation failed for {alert.uid}: {str(e)}")
            raise

    def update_alert_version(
        self, uid: str, new_version: int, updated_by: str
    ) -> AlertRuleVersion:
        """Track alert rule changes"""
        if new_version <= self.get_alert_version(uid):
            raise ValueError("Version must increment")

        version = AlertRuleVersion(version=new_version, updated_by=updated_by)

        # Store version in DB
        return version

    def get_alert_version(self, uid: str) -> int:
        """Get current version of alert"""
        # Implementation would fetch from DB
        return 1

    def _validate_alert_response(self, response: dict[str, Any]) -> bool:
        """Validate Grafana alert API response"""
        required_keys = {"uid", "title", "condition"}
        if not all(key in response for key in required_keys):
            raise ValueError(
                f"Alert response missing required keys: {required_keys - response.keys()}"
            )
        return True

import requests

from app.core.config import settings


class GrafanaConfig:
    """Grafana-specific configuration"""

    # Import from main settings
    PORT: int = settings.monitoring.GRAFANA_PORT
    SERVICE_URL: str = settings.monitoring.GRAFANA_URL
    API_KEY: str = settings.monitoring.GRAFANA_API_KEY
    SSL_CONFIG: dict = {"verify": False}
    RETRY_CONFIG: dict = {
        "stop_max_attempt_number": 3,
        "wait_exponential_multiplier": 1000,
    }
    # Additional configurations
    HEALTH_TIMEOUT: int = 30
    DASHBOARD_PATH: str = "/etc/grafana/provisioning/dashboards"
    UPDATE_INTERVAL: int = 10
    DEFAULT_LABELS: dict = {
        "service": "lead_ignite",
        "environment": settings.global_settings.ENVIRONMENT,
    }
    MULTIPROC_DIR: str = "/tmp/prometheus"
    CIRCUIT_BREAKER_CONFIG = {
        "failure_threshold": 5,
        "recovery_timeout": 300,
        "expected_exception": (requests.exceptions.RequestException,),
    }

    POOL_CONNECTIONS = 20
    POOL_MAXSIZE = 100
    MAX_RETRIES = 3
    CONNECT_TIMEOUT = 3.05
    READ_TIMEOUT = 30.0

# Grafana Integration: Best Usage Guide

This guide covers the best practices and recommended workflows for using Grafana with your backend, including provisioning, dashboard management, metrics, and alerting.

---

## 1. Provisioning Dashboards & Datasources
- **Location:** `provisioning/dashboards.yaml`, `provisioning/datasources.yaml`
- Define dashboards and datasources as code for repeatable, versioned infrastructure.
- Place JSON dashboard definitions in `provisioning/dashboards/` and datasource configs in `provisioning/datasources/`.

**Example:**
```yaml
# provisioning/dashboards.yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
```

---

## 2. Automated Dashboard Deployment
- **Script:** `deploy_dashboards.sh`
- Use this script to automate the deployment of dashboards to Grafana.
- Supports CI/CD integration for seamless updates.

---

## 3. Python Integration & API Usage
- **Client:** `client.py`
- Programmatically manage dashboards, datasources, and alerts using the Grafana HTTP API.
- Use `dashboard_manager.py` for CRUD operations on dashboards.
- Use `alert_manager.py` to manage alert rules.

**Example:**
```python
from app.core.grafana.client import GrafanaClient
client = GrafanaClient(base_url, api_key)
client.create_dashboard(dashboard_json)
```

---

## 4. Metrics & Monitoring
- **metrics.py:** Exposes Prometheus metrics for your backend.
- Integrate with Prometheus and configure Grafana panels to visualize application, database, and infrastructure metrics.
- Use the metrics endpoint in your backend for real-time monitoring.

---

## 5. Alerting
- **alert_manager.py:** Manage alert rules and notifications.
- Configure notifiers in `provisioning/notifiers/` for Slack, email, PagerDuty, etc.
- Use `exceptions.py` for custom error handling and alert escalation logic.

---

## 6. Models & Config
- **models.py:** Contains data models for dashboards, alerts, and datasources.
- **config.py:** Centralizes configuration for Grafana integration (URLs, API keys, etc.).

---

## 7. Backup & Restore
- **backup.py:** Automate backup of dashboards and Grafana configuration for disaster recovery.

---

## 8. Best Practices
- **Version Control:** Store all provisioning files, dashboards, and scripts in Git.
- **CI/CD:** Automate dashboard and datasource deployment as part of your deployment pipeline.
- **Monitoring:** Use Prometheus + Grafana for full-stack observability (application, DB, cache, infra).
- **Alerting:** Set up actionable, non-flaky alerts and test them regularly.
- **Security:** Store API keys and secrets securely (environment variables, vault, etc.).
- **Documentation:** Keep this usage guide and all dashboard definitions up to date.

---

For more details, see the code and docstrings in each file, and refer to the official [Grafana documentation](https://grafana.com/docs/).

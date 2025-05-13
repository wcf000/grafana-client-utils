# Grafana Monitoring - Production Ready

## ✅ Production Features

- **Dashboard Management**

  - Organized by functional areas (FastAPI, Databases, Business, etc.)
  - Version-controlled JSON definitions
  - Automatic provisioning via `dashboards.yaml`

- **Alerting System**

  - Multi-channel notifications:
    - Slack: `#alerts-prod`
    - PagerDuty: Critical incidents
    - Email: Team notifications
  - Environment-based configuration

- **Security**

  - Credentials via `${ENV_VARS}`
  - UI edits disabled in production
  - Deletion protection enabled

- **Performance**
  - Optimized refresh intervals (30-60s)
  - Query timeouts configured
  - Efficient metric selections

## 🛠️ Deployment

```bash
# Apply configurations
./deploy_dashboards.sh

# Verify health
curl -I ${GRAFANA_URL}/api/health
```

## 📁 Folder Structure & Conventions

```
grafana/
├── _docs/           # Markdown docs, best practices, diagrams, usage
├── _tests/          # Unit/integration tests for all core logic
├── config.py        # Singleton config (class-based, imports from global settings)
├── docker/          # Dockerfile, docker-compose, provisioning config, env
├── <core>.py        # Main implementation (alert_manager.py, metrics.py, etc.)
├── README.md        # Main readme (this file)
├── provisioning/    # (If applicable) Dashboard, datasource, notifier configs
```

- **_docs/**: All documentation, diagrams, and best practices for this integration.
- **_tests/**: All tests for this integration, including smoke, security, and metrics tests.
- **config.py**: Singleton config pattern, imports from global settings, exposes all constants for this integration.
- **docker/**: Containerization assets (Dockerfile, docker-compose, provisioning configs, .env.example, etc).
- **provisioning/**: (Grafana-specific) Dashboard, datasource, and alert channel configs.
- **<core>.py**: Main implementation modules (e.g., alert_manager.py, metrics.py, client.py, etc).

---

## 🏗️ Singleton & Config Pattern
- Use a single class (e.g., `GrafanaConfig`) in `config.py` to centralize all env, API, and integration settings.
- Import from global settings to avoid duplication and ensure DRY config.
- Document all config keys in `_docs/usage.md` and in this README.

---

## 📄 Documentation & Testing
- Place all best practices, diagrams, and usage guides in `_docs/`.
- All tests (unit, integration, smoke, security) go in `_tests/` with clear naming.
- Use `_tests/_docs/` for test-specific docs if needed.

---

## 🐳 Docker & Provisioning
- Place Dockerfile(s), docker-compose, and provisioning configs in `docker/`.
- Provide `.env.example` for local/dev/prod setups.
- Use `provisioning/` for Grafana dashboards, datasources, notifiers.

---

##  Required Environment Variables

```bash
# Prometheus
PROMETHEUS_SERVICE_URL=your_prometheus_url
PROMETHEUS_PASSWORD=your_password

# Alerting
SLACK_WEBHOOK_URL=your_webhook
PAGER_DUTY_CRITICAL_KEY=your_pagerduty_key
ALERT_EMAILS=team@company.com
```

---

## 🚨 Incident Response

1. Check Grafana dashboards for anomalies
2. Review corresponding alert channel:
   - Critical: PagerDuty
   - Warning: Slack
   - Info: Email
3. Consult dashboard-specific READMEs for troubleshooting

---

## 📈 Next Steps

- Set up dashboard version backups
- Configure monitoring for Grafana itself
- Establish dashboard review cadence


## 🔐 Required Environment Variables

refer to .env.example
```bash
# Prometheus
PROMETHEUS_SERVICE_URL=your_prometheus_url
PROMETHEUS_PASSWORD=your_password

# Alerting
SLACK_WEBHOOK_URL=your_webhook
PAGER_DUTY_CRITICAL_KEY=your_pagerduty_key
ALERT_EMAILS=team@company.com
```

## 🚨 Incident Response

1. Check Grafana dashboards for anomalies
2. Review corresponding alert channel:
   - Critical: PagerDuty
   - Warning: Slack
   - Info: Email
3. Consult dashboard-specific READMEs for troubleshooting

## 📈 Next Steps

- Set up dashboard version backups
- Configure monitoring for Grafana itself
- Establish dashboard review cadence

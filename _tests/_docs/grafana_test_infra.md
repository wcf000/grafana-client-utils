# Grafana Test Infra: Health, Running, and Debugging Guide

## How We Got Grafana Test Infra Running and Healthy

### 1. **Session-Scoped Docker Fixture**
- We implemented a single, robust, session-scoped `grafana_docker` fixture in `conftest.py`.
- This fixture:
  - Starts Grafana via Docker Compose before any tests run.
  - Waits for Grafana to become healthy by polling `/api/health` on both `127.0.0.1` and `localhost`.
  - If Grafana is not healthy in time, tests are skipped and the container is torn down.
  - Tears down the Grafana container after all tests complete.
- All print/logging uses `flush=True` for immediate feedback.
- All obsolete/duplicate fixtures (like `ensure_grafana_healthy`) were removed to prevent conflicts and double teardowns.

### 2. **Health Check Logic**
- Health checks are performed using the `requests` library to hit the Grafana API.
- The check is retried every few seconds up to a maximum timeout (default: 60s).
- If the health check fails, tests are skipped with a clear message.

### 3. **Environment & Security**
- Grafana admin credentials and API keys are set via environment variables.
- Sensitive values are not hardcoded.
- Default secrets are warned about at startup.

### 4. **Prometheus Metrics Isolation**
- Each test session uses a fresh `CollectorRegistry` to avoid metric duplication.
- This keeps metrics clean and prevents test interference.

---

## How to Fix Tests Failing in This Directory

### **Common Causes & Fixes**

1. **Grafana Not Healthy / Tests Skipped**
   - Check Docker Compose logs: `docker compose -f app/core/grafana/docker/docker-compose.grafana.yml logs`
   - Ensure port 3000 is not in use by another process.
   - Make sure Docker is running and you have permission to run containers.
   - If you see `Default SECRET_KEY detected`, set a secure `SECRET_KEY` in your environment.

2. **CollectorRegistry Not Defined**
   - Ensure `from prometheus_client import CollectorRegistry` is imported at the top of `conftest.py`.
   - Install the dependency: `poetry add prometheus_client`

3. **Import Errors (pytest, requests, prometheus_client)**
   - Make sure all dependencies are in your Poetry environment:
     ```bash
     poetry add pytest requests prometheus_client
     ```

4. **Test-Specific Failures**
   - Read the test output for specific assertion errors.
   - Use `-s` with pytest to see all print/log output.
   - If a test fails due to Grafana API, check if Grafana is healthy and credentials are correct.

5. **Container Cleanup**
   - If containers hang or tests fail to start, run:
     ```bash
     docker compose -f app/core/grafana/docker/docker-compose.grafana.yml down --remove-orphans
     ```
   - Then re-run your tests.

---

## TL;DR Checklist
- [x] Only one session-scoped, autouse Grafana fixture in `conftest.py`.
- [x] Health check logic robust and uses both 127.0.0.1 and localhost.
- [x] All dependencies (`pytest`, `requests`, `prometheus_client`) installed in Poetry.
- [x] Environment variables set for secrets and credentials.
- [x] Use `docker compose logs` for debugging container issues.

---

**If you encounter new errors, paste the stack trace and output here for targeted help!**

---

*Maintained by Ty the Programmer. Last updated: 2025-05-12.*

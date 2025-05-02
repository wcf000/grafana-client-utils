# Grafana Test Suite - Docker Execution Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Running Unit Tests](#running-unit-tests)
3. [Running Performance Tests](#running-performance-tests)
4. [Distributed Testing](#distributed-testing)
5. [Monitoring & Metrics](#monitoring--metrics)
6. [Troubleshooting](#troubleshooting)

## Prerequisites
- Docker and Docker Compose installed
- `docker-compose.test.yml` in project root
- Environment variables set:
  ```bash
  export GRAFANA_URL=http://localhost:3000
  export GRAFANA_API_KEY=your_api_key
  ```

## Running Unit Tests
```bash
docker-compose -f docker-compose.test.yml run --rm backend \
  pytest app/core/grafana/_tests -v
```

## Running Performance Tests
```bash
docker-compose -f docker-compose.test.yml up -d grafana prometheus redis

# Run Locust master
docker-compose -f docker-compose.test.yml run --rm backend \
  python app/core/grafana/_tests/run_distributed_locust.py --master --users 1000

# Run Locust workers (in separate terminals)
docker-compose -f docker-compose.test.yml run --rm backend \
  python app/core/grafana/_tests/run_distributed_locust.py --worker --host locust-master
```

## Monitoring & Metrics
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090
- Locust UI: http://localhost:8089

## Troubleshooting
1. **Test Failures**
   - Verify Grafana is running
   - Check API key permissions
   - Inspect logs: `docker-compose -f docker-compose.test.yml logs`

2. **Performance Issues**
   - Monitor resource usage: `docker stats`
   - Scale workers: Add more `locust-worker` services

3. **Common Errors**
   - Connection refused: Check service ports
   - Auth failures: Verify `GRAFANA_API_KEY`
   - Timeouts: Increase `--spawn-rate` gradually

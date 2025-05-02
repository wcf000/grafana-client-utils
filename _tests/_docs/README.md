# Grafana Performance Tests

This directory contains k6 performance tests for Grafana dashboards and alerts.

## Production Readiness Checklist
✅ Comprehensive test coverage  
✅ Automated test data cleanup  
✅ Distributed performance testing  
✅ CI/CD integration ready  
✅ Monitoring and metrics  
✅ Documentation

## Test Types
- **Smoke tests**: Basic functionality verification
- **Load tests**: Simulate expected production traffic
- **Stress tests**: Identify breaking points
- **Soak tests**: Long-running reliability tests
- **Negative tests**: Invalid inputs, error handling
- **Performance tests**: Locust-based benchmarks

## Test Coverage

| Test Category      | Files Covered | Key Metrics Tested |
|--------------------|---------------|--------------------|
| Alerting          | alert.py      | Notification channels, alert rules |
| Security          | security_test.py | Authentication, API key validation |
| Metrics           | metrtics.py   | Prometheus metrics collection |
| Smoke Testing     | smoke-test.py | Dashboard availability |

## Key Features
- Automatic cleanup of test data
- Environment-aware testing (prod/staging)
- Real-time performance metrics
- Distributed test execution
- Detailed error logging

## Execution

### Local Development
```bash
# Run all tests
pytest app/core/grafana/_tests

# Run specific test category
pytest app/core/grafana/_tests/alert.py
```

### CI/CD Integration
Tests automatically run on:
- Push to main branch
- Pull requests
- Scheduled nightly runs

## Monitoring

Key metrics tracked:
- `grafana_api_response_seconds`
- `test_success_total`
- `test_failure_total`

## Performance Testing with Locust

### Running Locust Tests
```bash
# Start Locust
locust -f app/core/grafana/_tests/locust_performance.py

# Run with specific user count
locust -f app/core/grafana/_tests/locust_performance.py --users 100 --spawn-rate 10
```

### Key Metrics
- Requests per second
- Response times (p50, p95, p99)
- Failure rates

### Negative Test Cases
Added in security_test.py:
- Malformed API keys
- Rate limiting
- Empty/invalid parameters

## Distributed Performance Testing

### Running Distributed Tests
```bash
# On master node
python run_distributed_locust.py --master --users 1000 --spawn-rate 50

# On worker nodes (run on separate machines)
python run_distributed_locust.py --worker --host <MASTER_IP>
```

### Configuration
- `LOCUST_MASTER_HOST`: Master node IP (default: localhost)
- `LOCUST_MASTER_PORT`: Master port (default: 5557)
- `ENVIRONMENT`: Target environment (prod/staging)

### Monitoring
- Real-time stats available at http://<MASTER_IP>:8089
- Detailed logs from all worker nodes

## Running Tests
```bash
# Run all tests
pytest app/core/grafana/_tests

# Run distributed performance tests
python app/core/grafana/_tests/run_distributed_locust.py --master
python app/core/grafana/_tests/run_distributed_locust.py --worker --host <master-ip>
```

## Monitoring
- Grafana dashboards for test metrics
- Prometheus metrics endpoint
- Real-time Locust web UI

## Maintenance
- Tests automatically clean up after themselves
- Tag test resources with "test-" prefix
- Session-level cleanup in conftest.py

## Troubleshooting

Common issues:
1. Authentication failures - Verify GRAFANA_API_KEY
2. Dashboard not found - Check UID matches test
3. Metrics server port conflicts - Change METRICS_PORT

## Best Practices
- Always mock external dependencies in unit tests
- Use fixtures for shared test resources
- Tag tests with @pytest.mark.category
- Monitor test flakiness rates

## Requirements
- k6 (https://k6.io/docs/get-started/installation/)
- Docker (optional)

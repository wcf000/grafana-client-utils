# _tests/smoke-test.py
import time

from metrics import API_RESPONSE_TIME, TEST_FAILURE, TEST_SUCCESS


def test_dashboard_availability(grafana_client):
    start_time = time.time()
    test_name = "test_dashboard_availability"
    try:
        response = grafana_client.dashboard.get_dashboard("fastapi")
        API_RESPONSE_TIME.labels(
            endpoint="/api/dashboards", status=response.status_code
        ).set(time.time() - start_time)
        TEST_SUCCESS.labels(test_name=test_name).inc()
    except Exception as e:
        TEST_FAILURE.labels(test_name=test_name, error=str(e)).inc()
        raise

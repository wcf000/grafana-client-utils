# security_test.py
import pytest
import requests
from app.core.config import settings

def test_authentication():
    response = requests.get("http://localhost:3000/api/dashboards/uid/fastapi")
    assert response.status_code == 401

def test_invalid_api_key():
    headers = {"Authorization": "Bearer invalid_key"}
    response = requests.get(
        "http://localhost:3000/api/dashboards/uid/fastapi", 
        headers=headers
    )
    assert response.status_code == 403

def test_malformed_api_key():
    headers = {"Authorization": "Bearer invalid!@#$%^"}
    response = requests.get(
        "http://localhost:3000/api/dashboards/uid/fastapi",
        headers=headers
    )
    assert response.status_code == 400

def test_rate_limiting():
    headers = {"Authorization": f"Bearer {settings.GRAFANA_API_KEY}"}
    for _ in range(10):
        requests.get(
            "http://localhost:3000/api/dashboards/uid/fastapi",
            headers=headers
        )
    response = requests.get(
        "http://localhost:3000/api/dashboards/uid/fastapi",
        headers=headers
    )
    assert response.status_code == 429

def test_empty_dashboard_uid():
    headers = {"Authorization": f"Bearer {settings.GRAFANA_API_KEY}"}
    response = requests.get(
        "http://localhost:3000/api/dashboards/uid/",
        headers=headers
    )
    assert response.status_code == 404

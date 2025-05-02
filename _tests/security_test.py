# security_test.py
import pytest
import requests


def test_authentication():
    response = requests.get("http://localhost:3000/api/dashboards/uid/fastapi")
    assert response.status_code == 401  # Unauthorized


def test_invalid_api_key():
    headers = {"Authorization": "Bearer invalid_key"}
    response = requests.get(
        "http://localhost:3000/api/dashboards/uid/fastapi", headers=headers
    )
    assert response.status_code == 403

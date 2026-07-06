import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_home():
    repsonse = client.get("/")
    assert repsonse.status_code == 200
    assert "Document Portal" in repsonse.text



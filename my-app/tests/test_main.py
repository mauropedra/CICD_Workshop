import pytest
import json
from app import app as flask_app

@pytest.fixture
def app():
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

def test_health_status_code(app, client):
    res = client.get('/healthcheck')
    assert res.status_code == 200
    expected = {'health_status': 'OK'}
    assert expected == json.loads(res.get_data(as_text=True))

def test_main_status_code(app, client):
    res = client.get('/')
    assert res.status_code == 200
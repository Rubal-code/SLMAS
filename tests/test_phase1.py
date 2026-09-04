from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_create_task_endpoint():
    response = client.post('/tasks', json={'goal_text': 'Learn from user feedback'})
    assert response.status_code == 201
    data = response.json()
    assert 'task_id' in data
    assert data['goal_text'] == 'Learn from user feedback'
    assert 'steps' in data

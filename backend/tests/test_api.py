from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'

def test_generate_post():
    response = client.post('/api/generate', json={'topic': 'Sustainable fashion', 'platform': 'Instagram', 'tone': 'Friendly'})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['title']
    assert data['caption']
    assert data['hashtags']
    assert data['call_to_action']
    assert data['image_prompt']
    assert data['image_data'].startswith('data:image/svg+xml;base64,')
    assert data['sources']
    assert data['id'] is not None

def test_invalid_topic():
    response = client.post('/api/generate', json={'topic': 'x'})
    assert response.status_code == 422

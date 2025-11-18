import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))


from fastapi.testclient import TestClient

from schemas import WeightScheme

from app.main import app

client = TestClient(app)

def test_get_all_datasets():
    response = client.get("/dataset")
    assert response.status_code == 200


def test_input_weights():
    response = client.get("dataset/weights")
    assert response.status_code == 200
    assert response.json() == {
        10: 0.15,
        20: 0.20,
        30: 0.20,
        40: 0.15,
        50: 0.15,
        60: 0.15,
    }
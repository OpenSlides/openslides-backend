from openslides_backend.datastore.shared.flask_frontend import get_health_url
from openslides_backend.datastore.writer.flask_frontend.routes import (
    RESERVE_IDS_URL,
    URL_PREFIX,
    WRITE_URL,
    WRITE_WITHOUT_EVENTS_URL,
)


def test_health_route(client):
    response = client.get(get_health_url(URL_PREFIX))
    assert response.status_code == 200


def test_wrong_method_write(client):
    response = client.get(WRITE_URL)
    assert response.status_code == 405


def test_wrong_method_reserve_ids(client):
    response = client.get(RESERVE_IDS_URL)
    assert response.status_code == 405


def test_wrong_method_write_without_events(client):
    response = client.get(WRITE_WITHOUT_EVENTS_URL)
    assert response.status_code == 405


def test_404_on_unknown_url_1(client):
    response = client.get("/")
    assert response.status_code == 404
    response = client.post("/", data={})
    assert response.status_code == 404


def test_404_on_unknown_url_2(client):
    response = client.get("/some/url")
    assert response.status_code == 404
    response = client.post("/some/url", data={})
    assert response.status_code == 404

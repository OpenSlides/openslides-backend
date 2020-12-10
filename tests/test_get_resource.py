# Tests for the openslides media service
import requests

GET_URL = "http://media:9006/system/media/get_resource/"


def test_positiv():
    # wait the service to start
    req = requests.get(GET_URL + "2")
    assert req.status_code == 200
    assert req.content == b"a2"
    assert "text/plain" in req.headers.get("Content-Type")


def test_not_found():
    req = requests.get(GET_URL + "1")
    assert req.status_code == 500
    assert "message" in req.json()


def test_invalid_responses():
    for i in (10, 11, 12, 13, 14):
        req = requests.get(GET_URL + str(i))
        assert req.status_code == 500
        assert "message" in req.json()


def test_not_ok_from_presenter():
    req = requests.get(GET_URL + "20")
    assert req.status_code == 404
    assert "message" in req.json()

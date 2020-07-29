# Tests for the openslides media service
import requests

def test_mediaservice_positiv():
    # wait the service to start
    req = requests.get('http://media:9006/system/media/get/2/test')
    assert req.status_code == 200
    assert req.content == b'a2'
    assert 'text/plain' in req.headers.get('Content-Type')


def test_mediaservice_not_found():
    req = requests.get('http://media:9006/system/media/get/4/test')
    assert req.status_code == 500


def test_mediaservice_auth_problem():
    req = requests.get('http://media:9006/system/media/get/12/test')
    assert req.status_code == 500

# Tests for the openslides media service
import requests
import time

def test_mediaservice_positiv():
    # wait the service to start
    time.sleep(10)
    req = requests.get('http://media:8000/system/media/get/3/test')
    assert req.status_code == 200


def test_mediaservice_not_found():
    time.sleep(10)
    req = requests.get('http://media:8000/system/media/get/4/test')
    assert req.status_code == 500


def test_mediaservice_auth_problem():
    time.sleep(10)
    req = requests.get('http://media:8000/system/media/get/12/test')
    assert req.status_code == 500

from .base import get_mediafile


def test_positiv():
    response = get_mediafile(2)
    assert response.status_code == 200
    assert response.content == b"a2"
    assert "text/plain" in response.headers.get("Content-Type")


def test_not_found():
    response = get_mediafile(1)
    assert response.status_code == 404
    assert "message" in response.json()


def test_invalid_responses():
    for i in (10, 11, 12, 13, 14):
        response = get_mediafile(i)
        assert response.status_code == 500
        assert "message" in response.json()


def test_not_ok_from_presenter():
    response = get_mediafile(20)
    assert response.status_code == 404
    assert "message" in response.json()


def test_redirect_if_not_logged_in():
    response = get_mediafile(2, use_cookie=False)
    assert response.status_code == 302
    assert response.headers["Location"] == "/"

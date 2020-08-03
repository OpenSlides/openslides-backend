import os

import requests

from .exceptions import NotFoundError, ServerError


def get_mediafile_id(meeting_id, path, app, cookie):
    presenter_url = get_presenter_url(meeting_id, path)
    app.logger.debug(f"Send check request: {presenter_url}")
    payload = [
        {
            "presenter": "get_mediafile_id",
            "data": {"meeting_id": meeting_id, "path": path},
        }
    ]

    try:
        response = requests.post(
            presenter_url, headers={"Cookie": cookie}, json=payload
        )
    except requests.exceptions.ConnectionError as e:
        app.logger.error(str(e))
        raise ServerError("The server didn't respond")

    if response.status_code in (requests.codes.forbidden, requests.codes.not_found):
        raise NotFoundError()
    if response.status_code != requests.codes.ok:
        raise ServerError(
            f"The server responded with an unexpected code "
            f"{response.status_code}: {response.content}"
        )

    try:
        id = int(response.json()[0])
    except Exception:
        raise ServerError("The Response did not contain a valid id.")
    return id


def get_presenter_url(meeting_id, path):
    presenter_host = os.environ.get("PRESENTER_HOST")
    presenter_port = os.environ.get("PRESENTER_PORT")
    if presenter_host is None:
        raise ServerError("PRESENTER_HOST is not set")
    if presenter_port is None:
        raise ServerError("PRESENTER_PORT is not set")
    return f"http://{presenter_host}:{presenter_port}/system/presenter"

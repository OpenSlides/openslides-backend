import os

import requests

from .exceptions import NotFoundError, ServerError


def get_mediafile_id(meeting_id, path, app, presenter_headers):
    presenter_url = get_presenter_url(app, meeting_id, path)
    app.logger.debug(f"Send check request: {presenter_url}")
    payload = [
        {
            "presenter": "get_mediafile_id",
            "data": {"meeting_id": meeting_id, "path": path},
        }
    ]

    try:
        response = requests.post(presenter_url, headers=presenter_headers, json=payload)
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
        raise NotFoundError("The Response did not contain a valid id.")
    return id


def get_presenter_url(app, meeting_id, path):
    presenter_host = app.config["PRESENTER_HOST"]
    presenter_port = app.config["PRESENTER_PORT"]
    return f"http://{presenter_host}:{presenter_port}/system/presenter"

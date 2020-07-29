import requests

from .exceptions import NotFoundError, ServerError


def get_mediafile_id(meeting_id, path, app, cookie):
    return meeting_id

    # TODO: Enable the call to the presenter
    check_request_url = get_check_request_url(meeting_id, path, app)
    app.logger.debug(f"Send check request: {check_request_url}")

    try:
        response = requests.post(check_request_url, headers={"Cookie": cookie})
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
        id = int(response.json()["id"])
    except Exception:
        raise ServerError("The Response did not contain a valid id.")
    return id


def get_check_request_url():
    presenter_host = "todo"
    presenter_port = "todo"
    return f"http://{presenter_host}:{presenter_port}/system/presenter"

import requests

from .exceptions import NotFoundError, ServerError


def get_mediafile_id(path, app, cookie):
    check_request_url = get_check_request_url(path, app)
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
            f"The server responded with an unexpected code {response.status_code}: {response.content}"
        )

    try:
        id = int(response.json()["id"])
    except Exception:
        raise ServerError("The Response did not contain a valid id.")
    return id


def get_check_request_url(path, app):
    check_request_url = app.config["CHECK_REQUEST_URL"]
    if path.startswith("/"):
        raise ServerError("The URL_PREFIX must begin and end with a slash.")
    if not check_request_url.endswith("/"):
        raise ServerError("The CHECK_REQUEST_URL must end with an slash.")
    return f"http://{check_request_url}{path}"

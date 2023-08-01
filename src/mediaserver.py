import atexit
import base64
import json
import sys
from functools import partial
from signal import SIGINT, SIGTERM, signal

from flask import Flask, Response, jsonify, redirect, request

from .auth import AUTHENTICATION_HEADER, check_file_id, check_login
from .config_handling import init_config, is_dev_mode
from .database import Database
from .exceptions import BadRequestError, HttpError, NotFoundError
from .logging import init_logging

app = Flask(__name__)
with app.app_context():
    init_logging()
    init_config()
    database = Database()

app.logger.info("Started media server")


@app.errorhandler(HttpError)
def handle_view_error(error):
    app.logger.error(
        f"Request to {request.path} resulted in {error.status_code}: "
        f"{error.message}"
    )
    res_content = {"message": f"Media-Server: {error.message}"}
    response = jsonify(res_content)
    response.status_code = error.status_code
    return response


@app.route("/system/media/get/<int:file_id>")
def serve(file_id):
    if not check_login():
        return redirect("/")

    # get file id
    presenter_headers = dict(request.headers)
    del_keys = [key for key in presenter_headers if "content" in key]
    for key in del_keys:
        del presenter_headers[key]
    ok, filename, auth_header = check_file_id(file_id, presenter_headers)
    if not ok:
        raise NotFoundError()

    app.logger.debug(f'Filename for "{file_id}" is {filename}')

    # Query file from db
    global database
    data, mimetype = database.get_file(file_id)

    # Send data (chunked)
    def chunked(size, source):
        for i in range(0, len(source), size):
            yield bytes(source[i : i + size])

    block_size = app.config["MEDIA_BLOCK_SIZE"]
    response = Response(chunked(block_size, data), mimetype=mimetype)
    # http headers can only be encoded using latin1
    filename_latin1 = filename.encode("latin1", errors="replace").decode("latin1")
    response.headers["Content-Disposition"] = f'inline; filename="{filename_latin1}"'

    client_cache_duration = int(app.config["MEDIA_CLIENT_CACHE_DURATION"] or 0)
    if client_cache_duration > 0 and not is_dev_mode():
        response.headers["Cache-Control"] = f"private, max-age={client_cache_duration}"

    if auth_header:
        response.headers[AUTHENTICATION_HEADER] = auth_header
    return response


@app.route("/internal/media/upload_mediafile/", methods=["POST"])
def media_post():
    dejson = get_json_from_request()
    try:
        file_data = base64.b64decode(dejson["file"].encode())
    except Exception:
        raise BadRequestError("cannot decode base64 file")
    try:
        file_id = int(dejson["id"])
        mimetype = dejson["mimetype"]
    except Exception:
        raise BadRequestError(
            f"The post request.data is not in right format: {request.data}"
        )
    app.logger.debug(f"to database {file_id} {mimetype}")
    global database
    database.set_mediafile(file_id, file_data, mimetype)
    return "", 200


@app.route("/internal/media/duplicate_mediafile/", methods=["POST"])
def duplicate_mediafile():
    source_id, target_id = get_ids(get_json_from_request())
    app.logger.debug(f"source_id {source_id} and target_id {target_id}")
    global database
    # Query file source_id from db
    data, mimetype = database.get_file(source_id)
    # Insert mediafile in target_id into db
    database.set_mediafile(target_id, data, mimetype)
    return "", 200


def get_json_from_request():
    try:
        decoded = request.data.decode()
        dejson = json.loads(decoded)
        return dejson
    except Exception:
        raise BadRequestError("request.data is not json")


def get_ids(dejson):
    try:
        source_id = int(dejson["source_id"])
        target_id = int(dejson["target_id"])
    except Exception:
        raise BadRequestError(
            f"The post request.data is not in right format: {request.data}"
        )
    return source_id, target_id


def shutdown(database):
    app.logger.info("Stopping the server...")
    database.shutdown()
    app.logger.info("Done!")


atexit.register(shutdown, database)

for sig in (SIGTERM, SIGINT):
    signal(sig, partial(sys.exit, 0))

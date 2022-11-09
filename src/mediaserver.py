import atexit
import base64
import json

from flask import Flask, Response, jsonify, request

from .auth import AUTH_HEADER, check_file_id
from .config_handling import init_config
from .database import Database
from .exceptions import BadRequestError, HttpError, NotFoundError
from .logging import init_logging

app = Flask(__name__)
init_logging(app)
init_config(app)
database = Database(app)

app.logger.info("Started Media-Server")


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


@app.route("/system/media/get/<int:mediafile_id>")
def serve(mediafile_id):
    return serve_files(mediafile_id, "mediafile")


@app.route("/system/media/get_resource/<int:resource_id>")
def serve_resource(resource_id):
    return serve_files(resource_id, "resource")


def serve_files(file_id, file_type):
    # get file id
    presenter_headers = dict(request.headers)
    del_keys = [key for key in presenter_headers if "content" in key]
    for key in del_keys:
        del presenter_headers[key]
    ok, filename, auth_header = check_file_id(
        file_id, file_type, app, presenter_headers
    )
    if not ok:
        raise NotFoundError()

    app.logger.debug(f'Filename for "{file_id}" is {filename}')

    # Query file from db
    global database
    data, mimetype = database.get_file(file_id, file_type)

    # Send data (chunked)
    def chunked(size, source):
        for i in range(0, len(source), size):
            yield bytes(source[i : i + size])

    block_size = app.config["MEDIA_BLOCK_SIZE"]
    response = Response(chunked(block_size, data), mimetype=mimetype)
    # http headers can only be encoded using latin1
    filename_latin1 = filename.encode('latin1',errors='replace').decode('latin1')
    response.headers["Content-Disposition"] = f'inline; filename="{filename_latin1}"'
    if auth_header:
        response.headers[AUTH_HEADER] = auth_header
    return response


@app.route("/internal/media/upload_mediafile/", methods=["POST"])
def media_post():
    return file_post("mediafile")


@app.route("/internal/media/upload_resource/", methods=["POST"])
def resource_post():
    return file_post("resource")


def file_post(file_type):
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
    app.logger.debug(f"to database {file_type} {file_id} {mimetype}")
    global database
    database.set_mediafile(file_id, file_type, file_data, mimetype)
    return "", 200


@app.route("/internal/media/duplicate_mediafile/", methods=["POST"])
def duplicate_mediafile():
    source_id, target_id = get_ids(get_json_from_request())
    app.logger.debug(f"source_id {source_id} and target_id {target_id}")
    global database
    # Query file source_id from db
    data, mimetype = database.get_file(source_id, "mediafile")
    # Insert mediafile in target_id into db
    database.set_mediafile(target_id, "mediafile", data, mimetype)
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

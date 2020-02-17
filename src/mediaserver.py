import atexit
import logging
import os
import sys

from flask import Flask, Response, request

from .auth import get_mediafile_id
from .database import Database
from .exceptions import HttpError, NotFoundError

# (name, type, default)
# If default is None, there is no default
all_configs = (
    ("URL_PREFIX", str, "/media/"),
    ("CHECK_REQUEST_URL", str, None),
    ("DB_HOST", str, None),
    ("DB_PORT", int, None),
    ("DB_NAME", str, None),
    ("DB_USER", str, None),
    ("DB_PASSWORD", str, None),
    ("BLOCK_SIZE", int, 4096),
)

app = Flask(__name__)

# Initialize logger:
# Adapt the gunicorn handlers, if gunicorn is used:
is_gunicorn = "gunicorn" in os.environ.get("SERVER_SOFTWARE", "")
if is_gunicorn:
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

# Read config.
try:
    app.config.from_pyfile("../config.py")
    app.logger.info("Found config.py. Loaded!")
except FileNotFoundError:
    app.logger.info(
        "Didn't find a config.py. Load settings from environment variables."
    )

# Load config from environment variables
for config, type, default in all_configs:
    if config not in app.config:
        value = os.environ.get(config, None)
        if not value and default is None:
            app.logger.critical(f"Did not find an environment variable for '{config}'")
            sys.exit(1)
        if not value:  # but we have a default
            value = default
        else:
            try:
                value = type(value)
            except Exception:  # noqa
                app.logger.critical(
                    f"Environment variable for '{config}' does not have the type {str(type)}"
                )
                sys.exit(1)
        app.config[config] = value

database = Database(app)

# Ready!
app.logger.info("Started Media-Server")


@app.errorhandler(HttpError)
def handle_view_error(error):
    app.logger.error(
        f"Request to {request.path} resulted in {error.status_code}: {error.message}"
    )
    return f"Media-Server: {error.message}", error.status_code


@app.route(app.config["URL_PREFIX"], defaults={"path": ""})
@app.route(f"{app.config['URL_PREFIX']}<path:path>")
def serve(path):
    if not path:
        raise NotFoundError()

    # get mediafile id
    cookie = request.headers.get("Cookie", "")
    id = get_mediafile_id(path, app, cookie)
    app.logger.debug(f'Id for "{path}" is {id}')

    # Query file from db
    global database
    data, mimetype = database.get_mediafile(id)

    # Send data (chunked)
    def chunked(size, source):
        for i in range(0, len(source), size):
            yield bytes(source[i : i + size])

    block_size = app.config["BLOCK_SIZE"]
    return Response(chunked(block_size, data), mimetype=mimetype)


def shutdown():
    app.logger.info("Stopping the server...")
    global database
    database.shutdown()
    app.logger.info("Done!")


atexit.register(shutdown)

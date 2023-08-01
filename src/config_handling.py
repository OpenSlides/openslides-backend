import os
import sys

from flask import current_app as app

DEV_MODE_ENVIRONMENT_VAR = "OPENSLIDES_DEVELOPMENT"
DEV_SECRET = "openslides"

CONFIG_DEFAULTS = {
    "MEDIA_DATABASE_HOST": "postgres",
    "MEDIA_DATABASE_PORT": 5432,
    "MEDIA_DATABASE_NAME": "openslides",
    "MEDIA_DATABASE_USER": "openslides",
    "MEDIA_DATABASE_PASSWORD_FILE": "/run/secrets/postgres_password",
    "MEDIA_BLOCK_SIZE": 4096,
    "MEDIA_CLIENT_CACHE_DURATION": 86400,
    "PRESENTER_HOST": "backend",
    "PRESENTER_PORT": 9003,
}


def get_type_for(config_value):
    return type(CONFIG_DEFAULTS[config_value])


def init_config():
    for config, default in CONFIG_DEFAULTS.items():
        if config.endswith("_FILE"):
            value = get_config_from(config)
        else:
            value = os.environ.get(config, default)
        if not value:
            app.logger.critical(f"Did not find an environment variable for '{config}'")
            sys.exit(1)
        config_type = type(default)
        try:
            value = config_type(value)
        except Exception:  # noqa
            app.logger.critical(
                f"Environment variable '{config}' does not have the type {str(config_type)}"
            )
            sys.exit(1)
        app.config[config.replace("_FILE", "")] = value


def is_dev_mode() -> bool:
    value = os.environ.get(DEV_MODE_ENVIRONMENT_VAR)
    return value is not None and value.lower() in ("1", "on", "true")


def get_config_from(config):
    path = os.environ.get(config, CONFIG_DEFAULTS[config])
    if is_dev_mode():
        return DEV_SECRET
    with open(path) as file_:
        return file_.read()

import os
import sys

MEDIA_DEV_MODE_ENVIRONMENT_VAR = "MEDIA_ENABLE_DEV_ENVIRONMENT"
DEV_SECRET = "openslides"


def get_type_for(config_value):
    if config_value in (
        "MEDIA_DATABASE_PORT",
        "MEDIA_BLOCK_SIZE",
        "PRESENTER_PORT",
    ):
        return int
    return str


def get_default_for(config_value):
    if config_value == "MEDIA_BLOCK_SIZE":
        return 4096


def init_config(app):
    file_configs = (
        "MEDIA_DATABASE_USER",
        "MEDIA_DATABASE_PASSWORD",
    )

    all_configs = (
        "MEDIA_DATABASE_HOST",
        "MEDIA_DATABASE_PORT",
        "MEDIA_DATABASE_NAME",
        "MEDIA_DATABASE_USER",
        "MEDIA_DATABASE_PASSWORD",
        "MEDIA_BLOCK_SIZE",
        "PRESENTER_HOST",
        "PRESENTER_PORT",
    )

    for config in all_configs:
        if config in file_configs:
            value = get_config_from(app, config)
        else:
            value = os.environ.get(config, get_default_for(config))
        if not value:
            app.logger.critical(f"Did not find an environment variable for '{config}'")
            sys.exit(1)
        try:
            value = get_type_for(config)(value)
        except Exception:  # noqa
            app.logger.critical(
                f"Environment variable for '{config}' does not have the "
                f"type {str(get_type_for(config))}"
            )
            sys.exit(1)
        app.config[config] = value


def is_dev_mode() -> bool:
    value = os.environ.get(MEDIA_DEV_MODE_ENVIRONMENT_VAR, None)
    return value is not None and value.lower() in ("1", "on", "yes", "true")


def get_config_from(app, config):
    path = os.environ.get(config + "_FILE", None)
    if is_dev_mode():
        value = DEV_SECRET
    elif path is not None:
        with open(path) as file_:
            value = file_.read()
    else:
        value = os.environ.get(config, None)
    return value

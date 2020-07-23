import sys
import os


def get_type_for(config_value):
    if config_value in ["DB_PORT", "BLOCK_SIZE"]:
        return int
    return str


def get_default_for(config_value):
    if config_value == "URL_PREFIX":
        return "/media/"
    if config_value == "BLOCK_SIZE":
        return 4096


def init_config(app):
    all_configs = ("URL_PREFIX", "CHECK_REQUEST_URL", "DB_HOST",
                   "DB_PORT", "DB_NAME", "DB_USER",
                   "DB_PASSWORD", "BLOCK_SIZE")

    for config in all_configs:
        value = os.environ.get(config, get_default_for(config))
        if not value:
            continue
        try:
            value = get_type_for(config)(value)
        except Exception:  # noqa
            app.logger.critical(
                f"Environment variable for '{config}' does not have the type {str(get_type_for(config))}"
            )
            sys.exit(1)
        app.config[config] = value

    if os.path.exists("../config.py"):
        app.config.from_pyfile("../config.py")
        app.logger.info("Found config.py. Loaded!")
    else:
        app.logger.info(
            "Didn't find a config.py. "
            "Use settings from environment variables."
        )

    for config in all_configs:
        if app.config[config] is None:
            app.logger.critical(
                f"Did not find an environment variable for '{config}'")
            sys.exit(1)

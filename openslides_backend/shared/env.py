import os


def is_dev_mode() -> bool:
    return bool(os.environ.get("OS4_DEVELOPMENT"))

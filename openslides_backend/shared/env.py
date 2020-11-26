import os


def is_truthy(value: str) -> bool:
    truthy = ("1", "on", "true")
    falsy = ("0", "off", "false")
    if value.lower() not in truthy + falsy:
        raise ValueError(f"Value must be one off {truthy + falsy}.")
    return value.lower() in truthy


def is_dev_mode() -> bool:
    dev = os.environ.get("OPENSLIDES_DEVELOPMENT", "off")
    return is_truthy(dev)

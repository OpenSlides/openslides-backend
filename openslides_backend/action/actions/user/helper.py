from typing import Any, Dict


def get_user_name(instance: Dict[str, Any]) -> str:
    """Methods gets short name, combined name or whatever you call it from
    instance-dict, which should contain first_name, last_name, username and title
    Analogue to __str__ method from Openslides3
    """
    first_name = instance.get("first_name", "").strip()
    last_name = instance.get("last_name", "").strip()

    if first_name and last_name:
        name = " ".join((first_name, last_name))
    else:
        name = first_name or last_name or instance.get("username", "")

    if title := instance.get("title", "").strip():
        name = " ".join([title, name])
    return name

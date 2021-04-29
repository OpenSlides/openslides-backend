from ...util.crypto import get_random_string


def get_user_token() -> str:
    return get_random_string(16)

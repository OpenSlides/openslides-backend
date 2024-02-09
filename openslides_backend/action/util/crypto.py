import secrets

RANDOM_STRING_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
PASSWORD_CHARS = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPRSTUVWXYZ23456789"


def get_random_string(length: int, allowed_chars: str = RANDOM_STRING_CHARS) -> str:
    """
    Return a securely generated random string.
    """
    return "".join(secrets.choice(allowed_chars) for i in range(length))


def get_random_password(length: int = 10, allowed_chars: str = PASSWORD_CHARS) -> str:
    """
    Return a securely generated random password which only uses easily identifiable characters.
    """
    return get_random_string(length, allowed_chars)

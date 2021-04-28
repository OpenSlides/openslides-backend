from secrets import choice

USER_TOKEN_LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def get_user_token() -> str:
    secrets_letter_list = [choice(USER_TOKEN_LETTERS) for _ in range(16)]
    return "".join(secrets_letter_list)

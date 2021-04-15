from random import choice

USER_TOKEN_LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def get_user_token() -> str:
    random_letter_list = [choice(USER_TOKEN_LETTERS) for _ in range(16)]
    return "".join(random_letter_list)

import secrets


def gen_id() -> int:
    return int(secrets.token_hex(8), 16)

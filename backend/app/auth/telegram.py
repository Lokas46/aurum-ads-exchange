import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl, unquote


class InvalidInitDataError(Exception):
    pass


class ExpiredInitDataError(Exception):
    pass


def validate_init_data(init_data: str, bot_token: str, expiration: int = 86400) -> dict:
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))

    if "hash" not in parsed:
        raise InvalidInitDataError("Missing hash parameter")
    if "auth_date" not in parsed:
        raise InvalidInitDataError("Missing auth_date parameter")

    auth_date = int(parsed["auth_date"])
    now = time.time()
    if now - auth_date > expiration:
        raise ExpiredInitDataError(
            f"Auth data expired: {int(now - auth_date)}s > {expiration}s"
        )
    if auth_date > now + 30:
        raise InvalidInitDataError("Auth date is in the future")

    hash_value = parsed.pop("hash")
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )

    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode(),
        hashlib.sha256,
    ).digest()

    computed_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, hash_value):
        raise InvalidInitDataError("Hash verification failed")

    if "user" in parsed:
        parsed["user"] = json.loads(unquote(parsed["user"]))

    return parsed

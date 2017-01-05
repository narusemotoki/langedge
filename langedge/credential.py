import hashlib
import hmac
import time
from typing import (
    Any,
    Dict,
)


class Credential:
    def __init__(self, url: str, public_key: str, private_key: str) -> None:
        self.url = url
        self.public_key = public_key
        self.private_key = private_key.encode()

    def sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        timestamp = str(int(time.time()))
        return dict(
            api_key=self.public_key,
            ts=timestamp,
            api_sig=hmac.new(self.private_key, timestamp.encode(), hashlib.sha1).hexdigest(),
            **params
        )

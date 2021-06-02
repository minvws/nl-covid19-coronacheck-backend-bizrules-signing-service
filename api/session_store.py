from base64 import b64encode
from typing import Dict, Optional, Union
from uuid import UUID, uuid4

import redis
from nacl.secret import SecretBox

from api.settings import AppSettings, RedisSettings, redis_settings, settings
from api.utils import hmac256


class SessionStore:
    def __init__(self, general_settings: AppSettings, backend_settings: RedisSettings):
        self._redis: redis.Redis = redis.Redis(**backend_settings.dict())
        self._hmac_key = general_settings.REDIS_HMAC_KEY
        self._box = SecretBox(general_settings.REDIS_NACL_SECRET_KEY)
        self._ex: int = general_settings.EXPIRATION_TIME_IN_SECONDS
        self._key_prefix: bytes = general_settings.REDIS_KEY_PREFIX.encode() + b":"

    def _hash_key(self, key: bytes) -> bytes:
        return self._key_prefix + b64encode(hmac256(key, self._hmac_key))

    def store_message(self, message: bytes, encrypt: bool = True) -> str:
        message = self._box.encrypt(message) if encrypt else message
        session_token = uuid4()
        self._redis.set(self._hash_key(session_token.bytes), message, ex=self._ex)
        return str(session_token)

    def get_message(self, session_token: str, decrypt: bool = True) -> Optional[bytes]:
        """

        Args:
            session_token: a string that was returned earlier by `store_prepare_issue_message`

        Returns:
            Either a list of nonces or None if the session token is no longer valid.
            By design the session token can be used only once to retreive the nonces.

        """
        key = self._hash_key(UUID(session_token).bytes)
        pipe = self._redis.pipeline()
        pipe.get(key)
        pipe.delete(key)
        message, _ = pipe.execute()
        if isinstance(message, bytes):
            message = self._box.decrypt(message) if decrypt else message
            return message
        return None

    def health_check(self) -> Dict[str, Union[bool, str]]:
        try:
            self._redis.ping()
            return {"is_healthy": True, "message": "ping succeeded"}
        except redis.exceptions.RedisError as err:
            return {"is_healthy": False, "message": repr(err)}


session_store = SessionStore(settings, redis_settings)

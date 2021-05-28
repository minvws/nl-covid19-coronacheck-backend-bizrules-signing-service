from typing import Dict, Optional, Union
from uuid import UUID, uuid4

import redis

from api.settings import AppSettings, RedisSettings, redis_settings, settings


class SessionStore:
    def __init__(self, general_settings: AppSettings, backend_settings: RedisSettings):
        self._redis: redis.Redis = redis.Redis(**backend_settings.dict())
        self._nonce_byte_security: int = general_settings.NONCE_BYTE_SECURITY
        self._ex: int = general_settings.EXPIRATION_TIME_IN_SECONDS
        self._key_prefix: bytes = general_settings.REDIS_KEY_PREFIX.encode() + b":"

    def store_message(self, message: bytes) -> str:
        session_token = uuid4()
        self._redis.set(self._key_prefix + session_token.bytes, message, ex=self._ex)
        return str(session_token)

    def get_message(self, session_token: str) -> Optional[bytes]:
        """

        Args:
            session_token: a string that was returned earlier by `store_prepare_issue_message`

        Returns:
            Either a list of nonces or None if the session token is no longer valid.
            By design the session token can be used only once to retreive the nonces.

        """
        key = self._key_prefix + UUID(session_token).bytes
        pipe = self._redis.pipeline()
        pipe.get(key)
        pipe.delete(key)
        message, _ = pipe.execute()
        if message is None:
            return None
        if isinstance(message, bytes):
            return message
        return None

    def health_check(self) -> Dict[str, Union[bool, str]]:
        try:
            self._redis.ping()
            return {"is_healthy": True, "message": "ping succeeded"}
        except redis.exceptions.RedisError as err:
            return {"is_healthy": False, "message": repr(err)}


session_store = SessionStore(settings, redis_settings)

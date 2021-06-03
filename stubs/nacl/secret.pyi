from typing import Optional, Any

class SecretBox(object):

    KEY_SIZE: int
    NONCE_SIZE: int
    MACBYTES: int
    MESSAGEBYTES_MAX: int
    def __init__(self, key: bytes, encoder: Any = ...): ...
    def encrypt(self, plaintext: bytes, nonce: Optional[bytes] = None, encoder: Any = ...) -> bytes: ...
    def decrypt(self, ciphertext: bytes, nonce: Optional[bytes] = None, encoder: Any = ...) -> bytes: ...

from __future__ import annotations
import base64, os
from typing import Tuple
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet


PBKDF2_ITERS_DEFAULT = 200_000
SALT_LEN = 16  # bytes


def make_salt(n: int = SALT_LEN) -> bytes:
    return os.urandom(n)


def derive_fernet_key(password: str, salt: bytes, iterations: int = PBKDF2_ITERS_DEFAULT) -> bytes:
    """Leitet aus Passwort+Salt einen 32-Byte-Key ab und verpackt ihn als Fernet-Key (urlsafe base64)."""
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=iterations)
    raw = kdf.derive(password.encode("utf-8"))
    return base64.urlsafe_b64encode(raw)  # Fernet erwartet base64url-encoded 32B


def make_fernet(key: bytes) -> Fernet:
    return Fernet(key)


def encrypt_bytes(plaintext: bytes, fkey: bytes) -> bytes:
    return make_fernet(fkey).encrypt(plaintext)


def decrypt_bytes(token: bytes, fkey: bytes) -> bytes:
    return make_fernet(fkey).decrypt(token)

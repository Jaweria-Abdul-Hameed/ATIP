"""Cryptographic utilities for securely encrypting and decrypting sensitive tokens at rest."""

import base64
import hashlib

from cryptography.fernet import Fernet

from atip_api.config import get_settings


def _get_fernet() -> Fernet:
    """Derive a stable 32-byte URL-safe base64 key from SECRET_KEY."""
    settings = get_settings()
    key_digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_digest)
    return Fernet(fernet_key)


def encrypt_secret(plaintext: str) -> str:
    """Encrypt a secret string into an opaque ciphertext string."""
    if not plaintext:
        return ""
    fernet = _get_fernet()
    encrypted = fernet.encrypt(plaintext.encode("utf-8"))
    return encrypted.decode("utf-8")


def decrypt_secret(ciphertext: str) -> str:
    """Decrypt an encrypted ciphertext string back to plaintext."""
    if not ciphertext:
        return ""
    fernet = _get_fernet()
    decrypted = fernet.decrypt(ciphertext.encode("utf-8"))
    return decrypted.decode("utf-8")

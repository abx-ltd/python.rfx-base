from cryptography.fernet import Fernet
from fluvius.fastapi import config

def get_fernet() -> Fernet:
    """Initialize a Fernet symmetric encryption context using the application secret."""
    key = config.APPLICATION_SECRET_KEY
    if not key:
        raise ValueError("APPLICATION_SECRET_KEY is not configured but is required for encryption.")
    # Pad or decode key if needed to ensure 32 url-safe base64 bytes
    try:
        return Fernet(key.encode('utf-8'))
    except ValueError as e:
        # If the key isn't perfectly Fernet-compatible by default, let's normalize it
        import base64
        import hashlib
        # Hash the key to exactly 32 bytes, then base64 encode it for Fernet
        hashed_key = hashlib.sha256(key.encode('utf-8')).digest()
        b64_key = base64.urlsafe_b64encode(hashed_key)
        return Fernet(b64_key)

def encrypt_password(password: str) -> str:
    """Encrypt a plaintext password for safe database storage."""
    f = get_fernet()
    return f.encrypt(password.encode('utf-8')).decode('utf-8')

def decrypt_password(encrypted_password: str) -> str:
    """Decrypt a database-stored password back to plaintext."""
    f = get_fernet()
    return f.decrypt(encrypted_password.encode('utf-8')).decode('utf-8')

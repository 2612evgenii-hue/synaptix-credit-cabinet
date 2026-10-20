"""Password hashing for demo seed only — not an HTTP auth layer."""

from passlib.context import CryptContext
from passlib.exc import UnknownHashError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Return False on mismatch or unparseable/empty hash (never raise)."""
    if not hashed or not isinstance(hashed, str):
        return False
    try:
        return bool(pwd_context.verify(plain, hashed))
    except (UnknownHashError, ValueError, TypeError):
        return False

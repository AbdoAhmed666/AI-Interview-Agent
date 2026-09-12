from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from config import settings
from typing import Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from crud import (
    get_user_by_email,
    get_user_by_id,
)
from database import get_db

from models import User

# JWT Configuration
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

# bcrypt only considers the first 72 bytes of a password; bcrypt >= 4.1 raises
# instead of silently truncating, so we truncate explicitly for consistent,
# version-independent behavior. We use the ``bcrypt`` library directly rather
# than passlib, which is unmaintained and breaks against modern bcrypt.
_BCRYPT_MAX_BYTES = 72


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
)


def _password_bytes(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    try:
        return bcrypt.checkpw(
            _password_bytes(plain_password),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )



def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
    except JWTError:
        return None
    
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:

    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
        )

    user = get_user_by_id(
        db,
        int(user_id),
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    return user
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from configs.base_config import BaseConfig
from fastapi import HTTPException, Request, status
from jose import JWTError, jwt


def verify_authentication(request: Request):
    """
    Verifies JWT from:
    1. Authorization header (Bearer token)
    2. Session (legacy / browser-based)
    """

    token = None

    # ------------------ Authorization Header ------------------
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]

    # ------------------ Session Fallback ------------------
    elif "loginer_details" in request.session:
        token = request.session["loginer_details"]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    try:
        payload = jwt.decode(
            token,
            BaseConfig.SECRET_KEY,
            algorithms=[BaseConfig.ALGORITHM],
        )
    except JWTError as exc:
        print(exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    user_id = payload.get("user_id")
    user_role = payload.get("user_role")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        )

    return user_id, user_role, token


def hash_text(plain_text: str) -> str:
    """
    Hash a given plain text using bcrypt.
    Returns hashed string.
    """
    if not plain_text:
        raise ValueError("Text to hash cannot be empty")

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_text.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_hash(plain_text: str, hashed_text: str) -> bool:
    """
    Verify plain text against bcrypt hash.
    """
    return bcrypt.checkpw(
        plain_text.encode("utf-8"),
        hashed_text.encode("utf-8"),
    )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=BaseConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, BaseConfig.SECRET_KEY, algorithm=BaseConfig.ALGORITHM
    )
    return encoded_jwt

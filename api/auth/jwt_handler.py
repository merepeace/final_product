import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

SECRET_KEY = os.getenv("WMS_JWT_SECRET", "wms-dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("WMS_JWT_EXPIRE_MINUTES", "480"))

ADMIN_USERNAME = os.getenv("WMS_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("WMS_ADMIN_PASSWORD", "admin")


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def verify_admin_credentials(username: str, password: str) -> bool:
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

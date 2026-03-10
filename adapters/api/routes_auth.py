from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt

from infrastructure.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _verify_password(plain: str) -> bool:
    return bcrypt.checkpw(plain.encode(), settings.admin_password_hash)


def _create_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode(
        {"sub": username, "exp": expire},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


@router.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    if form.username != settings.admin_username or not _verify_password(form.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": _create_token(form.username), "token_type": "bearer"}

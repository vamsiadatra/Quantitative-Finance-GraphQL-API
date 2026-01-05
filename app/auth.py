from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from strawberry.permission import BasePermission
from strawberry.types import Info
from fastapi import Request

SECRET_KEY = "super_secret_enterprise_key"
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=30)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        return None

# Strawberry Permission Class
class IsAuthenticated(BasePermission):
    message = "User is not authenticated"

    async def has_permission(self, source, info: Info, **kwargs) -> bool:
        request: Request = info.context["request"]
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return False
        token = auth_header.split(" ")[1] # Bearer <token>
        user = decode_token(token)
        return user is not None

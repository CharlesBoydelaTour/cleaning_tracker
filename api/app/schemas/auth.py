from pydantic import BaseModel, EmailStr, ConfigDict  # Ajout de ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserSignup(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

    model_config = ConfigDict(strict=True)


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    model_config = ConfigDict(strict=True)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[UUID] = None


class RefreshToken(BaseModel):
    refresh_token: str

    model_config = ConfigDict(strict=True)


class UserResponse(BaseModel):
    id: UUID  # Changer str en UUID
    email: str
    full_name: Optional[str] = None
    email_confirmed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        json_encoders={datetime: lambda dt: dt.isoformat() if dt else None},
        arbitrary_types_allowed=True,
    )


class AuthResponse(BaseModel):
    user: UserResponse
    tokens: Token

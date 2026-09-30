"""Pydantic schemas for authentication endpoints."""

import re
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator, model_validator

from app.models.user import UserRole


# ── Registration ──────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str
    role: UserRole = UserRole.FARMER

    @field_validator("full_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Full name must be at least 2 characters.")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number.")
        return v

    @field_validator("role")
    @classmethod
    def no_public_admin(cls, v: UserRole) -> UserRole:
        if v == UserRole.ADMIN:
            raise ValueError("Admin accounts cannot be created via public registration.")
        return v

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        digits = re.sub(r"[\s\-\(\)\+]", "", v)
        if not digits.isdigit() or not (7 <= len(digits) <= 15):
            raise ValueError("Phone number must be 7–15 digits.")
        return v


# ── Login ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.lower().strip()


# ── Token ─────────────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── User responses (never expose password_hash) ───────────────────────────────

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str]
    role: UserRole
    is_active: bool

    model_config = {"from_attributes": True}


class RegisterResponse(BaseModel):
    message: str
    user: UserResponse

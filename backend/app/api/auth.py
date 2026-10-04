"""
Authentication API routes.
  POST /api/auth/register
  POST /api/auth/login
  GET  /api/auth/me
  GET  /api/auth/test/farmer
  GET  /api/auth/test/buyer
  GET  /api/auth/test/admin
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.api.deps import get_current_user, require_role
from app.core.security import create_access_token, hash_password, verify_password
from app.database.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ── Register ──────────────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new farmer or buyer account",
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    # Check for duplicate email
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return RegisterResponse(
        message="Account created successfully.",
        user=UserResponse.model_validate(user),
    )


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive a JWT access token",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    # Deliberate generic message — do not reveal whether email exists
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not user or not user.password_hash:
        logger.warning("Login failed: email not found")
        raise invalid
    if not verify_password(payload.password, user.password_hash):
        logger.warning("Login failed: wrong password for user_id=%s", user.id if user else "?")
        raise invalid
    if not user.is_active:
        logger.warning("Login failed: inactive account user_id=%s", user.id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive.",
        )

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(access_token=token)


# ── Current user ──────────────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the currently authenticated user",
)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


# ── Role-test endpoints (development verification only) ───────────────────────

@router.get(
    "/test/farmer",
    summary="[Dev] Verify FARMER role access",
    dependencies=[Depends(require_role(UserRole.FARMER))],
)
def test_farmer():
    return {"message": "Farmer access verified"}


@router.get(
    "/test/buyer",
    summary="[Dev] Verify BUYER role access",
    dependencies=[Depends(require_role(UserRole.BUYER))],
)
def test_buyer():
    return {"message": "Buyer access verified"}


@router.get(
    "/test/admin",
    summary="[Dev] Verify ADMIN role access",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
def test_admin():
    return {"message": "Admin access verified"}

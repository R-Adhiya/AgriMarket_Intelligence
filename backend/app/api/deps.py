"""
FastAPI dependencies for authentication and role-based authorisation.
Import these in route files — never import from here into core/security.py.
"""

import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database.session import get_db
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Validates the bearer token and returns the authenticated User.
    Raises HTTP 401 on any invalid / expired / missing token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            logger.warning("JWT decode succeeded but 'sub' claim missing")
            raise credentials_exception
    except JWTError as e:
        logger.warning("JWT validation failed: %s", type(e).__name__)
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        logger.warning("JWT references unknown user_id=%s", user_id)
        raise credentials_exception
    if not user.is_active:
        logger.warning("Inactive user_id=%s attempted access", user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive.",
        )
    return user


def require_role(*roles: UserRole):
    """
    Dependency factory — returns a dependency that enforces role membership.

    Usage:
        @router.get("/farmer-only", dependencies=[Depends(require_role(UserRole.FARMER))])
        def farmer_only(): ...
    """
    def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            logger.warning(
                "Authorization denied: user_id=%s role=%s tried to access %s-only resource",
                current_user.id, current_user.role, [r.value for r in roles],
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )
        return current_user
    return _check

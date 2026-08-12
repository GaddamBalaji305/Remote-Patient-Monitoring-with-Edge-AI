from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import User
from backend.app.schemas import LoginRequest, TokenResponse, UserResponse
from backend.app.security.password import verify_password
from backend.app.security.auth import create_access_token
from backend.app.security.dependencies import get_current_user
from backend.app.services.audit_logger import audit_logger

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(request: Request, login_in: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user with email & password, returning signed JWT access token.
    Records security audit log on successful login.
    """
    user = db.query(User).filter(User.email == login_in.email).first()
    if not user or not verify_password(login_in.password, user.password_hash):
        client_ip = request.client.host if request.client else "127.0.0.1"
        audit_logger.log_event(
            db=db,
            action="USER_LOGIN_FAILED",
            ip_address=client_ip,
            details=f"Failed login attempt for email: {login_in.email}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email, "role": user.role, "id": user.id})
    
    # Record Audit Log
    client_ip = request.client.host if request.client else "127.0.0.1"
    audit_logger.log_event(
        db=db,
        user_id=user.id,
        action="USER_LOGIN_SUCCESS",
        ip_address=client_ip,
        details=f"User {user.email} signed in successfully with role {user.role}"
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Return currently authenticated user profile details.
    """
    return current_user

"""Authentication router - local + Google OAuth."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db
from app.crud import user as user_crud
from app.schemas.user import (
    RegisterRequest, LoginRequest, TokenResponse,
    UserResponse, RefreshTokenRequest, PasswordChangeRequest,
)
from app.core.security import (
    create_access_token, create_refresh_token, decode_token,
    get_current_user, hash_password, verify_password,
)
from app.core.config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user (admin, teacher, or student)."""
    if user_crud.get_user_by_email(db, data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if user_crud.get_user_by_username(db, data.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    user = user_crud.create_user_from_register(
        db,
        email=data.email,
        username=data.username,
        password=data.password,
        full_name=data.full_name,
        role=data.role,
        student_id_number=data.student_id_number,
    )
    return user


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Login with username/email and password."""
    user = user_crud.authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token."""
    payload = decode_token(data.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Invalid token type")

    user_id = payload.get("sub")
    user = user_crud.get_user(db, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    refresh_tok = create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_tok,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)):
    """Get current authenticated user."""
    return current_user


@router.post("/change-password")
def change_password(data: PasswordChangeRequest, current_user=Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """Change password."""
    if not current_user.hashed_pwd:
        raise HTTPException(status_code=400, detail="Google OAuth users cannot change password here")
    if not verify_password(data.old_password, current_user.hashed_pwd):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    current_user.hashed_pwd = hash_password(data.new_password)
    db.commit()
    return {"message": "Password changed successfully"}


# ============ GOOGLE OAuth ============

@router.get("/google/login")
def google_login(role: str = "student"):
    """Redirect to Google OAuth consent screen."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Google OAuth not configured")

    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}"
        "&response_type=code"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
        "&scope=openid%20email%20profile"
        f"&state={role}"
        "&access_type=offline"
    )
    return RedirectResponse(url=google_auth_url)


@router.get("/google/callback")
async def google_callback(code: str, state: str = "student", db: Session = Depends(get_db)):
    """Handle Google OAuth callback."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=501, detail="Google OAuth not configured")

    import httpx

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )

    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange Google auth code")

    token_data = token_response.json()
    id_token = token_data.get("id_token")

    # Decode Google ID token (without verification for simplicity; add verification in production)
    import jwt as pyjwt
    try:
        google_user = pyjwt.decode(id_token, options={"verify_signature": False})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Google token")

    google_id = google_user.get("sub")
    email = google_user.get("email")
    full_name = google_user.get("name", "")
    picture = google_user.get("picture", "")

    # Check if user exists
    user = user_crud.get_user_by_google_id(db, google_id)
    if not user:
        user = user_crud.get_user_by_email(db, email)
        if user:
            # Link Google account to existing user
            user.google_id = google_id
            user.auth_provider = "google"
            if picture:
                user.avatar_url = picture
            db.commit()
            db.refresh(user)
        else:
            # Create new user
            role = state if state in ("admin", "teacher", "student") else "student"
            user = user_crud.create_google_user(
                db, email=email, full_name=full_name,
                google_id=google_id, avatar_url=picture, role=role,
            )

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    refresh_tok = create_refresh_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_tok,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user).model_dump(),
    }

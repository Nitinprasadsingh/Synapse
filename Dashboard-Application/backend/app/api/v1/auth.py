from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.core.security import verify_password, create_access_token
from app.models.user import User
from app.schemas.auth import Token, UserLogin, UserResponse

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user via JSON body or OAuth2 form-data and return JWT token.
    """
    content_type = request.headers.get("content-type", "")
    username = ""
    password = ""

    if "application/json" in content_type:
        body = await request.json()
        username = body.get("email") or body.get("username", "")
        password = body.get("password", "")
    else:
        form = await request.form()
        username = form.get("username") or form.get("email", "")
        password = form.get("password", "")

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required"
        )

    user = db.query(User).filter(User.email == username.strip().lower()).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is inactive. Contact system administrator."
        )

    access_token = create_access_token(
        subject=user.id,
        role=user.role
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name
    )


@router.post("/logout")
def logout():
    """Client logout confirmation."""
    return {"message": "Successfully logged out. Client token invalidated."}


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    """Retrieve authenticated user profile and permissions."""
    return current_user

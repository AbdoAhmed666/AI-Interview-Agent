from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from crud import create_user, get_user_by_email
from database import get_db
from fastapi.security import OAuth2PasswordRequestForm
from models import User
from schemas import (
    Token,
    UserLogin,
    UserRegister,
    UserResponse,
)
from security import (
    create_access_token,
    hash_password,
    verify_password,
    get_current_user,
)


router = APIRouter(tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user: UserRegister,
    db: Session = Depends(get_db),
):

    existing_user = get_user_by_email(
        db,
        user.email,
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        )

    new_user = create_user(
        db=db,
        name=user.name,
        email=user.email,
        hashed_password=hash_password(user.password),
    )

    return new_user


@router.post(
    "/login",
    response_model=Token,
)
def login(
    user: UserLogin,
    db: Session = Depends(get_db),
):

    db_user = get_user_by_email(
        db,
        user.email,
    )

    if (
        not db_user
        or not verify_password(
            user.password,
            db_user.hashed_password,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token(
        {
            "sub": str(db_user.id),
            "email": db_user.email,
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }

@router.post(
    "/token",
    response_model=Token,
)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):

    db_user = get_user_by_email(
        db,
        form_data.username,
    )

    if (
        not db_user
        or not verify_password(
            form_data.password,
            db_user.hashed_password,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    access_token = create_access_token(
        {
            "sub": str(db_user.id),
            "email": db_user.email,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.app.core.security import (
    create_access_token,
    hash_password,
    verify_password
)
from src.app.core.deps import get_users_repo
from src.app.db.repositories import UsersRepository
from src.app.models.users import TokenResponse, UserCreate, UserOut


router = APIRouter()


@router.post("/register",
             response_model=UserOut,
             status_code=status.HTTP_201_CREATED)
async def register_user(
        user: UserCreate,
        users: UsersRepository = Depends(get_users_repo)
):
    user = user.model_dump()
    if await users.get_by_email(user.get('email')):
        raise HTTPException(status_code=409, detail='Email already registered')

    password_hash = hash_password(user.get('password'))
    creation_result = await users.create(user.get('email'), password_hash)
    created_user = UserOut.model_validate(creation_result)
    return created_user


@router.post("/jwt/login",
             response_model=TokenResponse)
async def login_user(
        user: UserCreate,
        users: UsersRepository = Depends(get_users_repo)
):
    user_by_email = await users.get_by_email(str(user.email))
    if user_by_email and verify_password(user.password, user_by_email.get('password_hash')):
        token = create_access_token(str(user_by_email['id']))
        payload = {
            "access_token": token
        }
        return TokenResponse.model_validate(payload)
    else:
        raise HTTPException(status_code=401, detail='LOGIN_BAD_CREDENTIALS')

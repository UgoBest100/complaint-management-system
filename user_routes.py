from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from models import UserCreate, User
from user_storage import load_users, save_users
from auth_utils import hash_password, verify_password, create_access_token

router = APIRouter(tags=["Users"])


@router.post("/register", response_model=User)
def register_user(payload: UserCreate):
    users: List[User] = load_users()

    # uniqueness checks
    if any(u.email.lower() == payload.email.lower() for u in users):
        raise HTTPException(status_code=400, detail="Email already registered.")
    if any(u.username.lower() == payload.username.lower() for u in users):
        raise HTTPException(status_code=400, detail="Username already taken.")

    if payload.role not in ("admin", "customer"):
        raise HTTPException(status_code=400, detail="Role must be 'admin' or 'customer'.")

    new_user = User(
        id=(max((u.id for u in users), default=0) + 1),
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role
    )
    users.append(new_user)
    save_users(users)
    return new_user


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Accepts username OR email in the `username` field of the form.
    """
    users = load_users()
    lookup = form_data.username
    # find by email OR username
    user = next(
        (u for u in users if u.email.lower() == lookup.lower() or u.username.lower() == lookup.lower()),
        None
    )
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username/email or password")

    token = create_access_token(data={"sub": user.email, "role": user.role, "username": user.username})
    return {"access_token": token, "token_type": "bearer"}

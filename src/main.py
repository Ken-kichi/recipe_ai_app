from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from src.api_models import User, UserInDB
from src.utils import get_current_active_user, fake_hash_password
from src.database import fake_users_db
from src.api.auth.index import router as auth_router
app = FastAPI()

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

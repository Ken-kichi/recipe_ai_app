from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.db_models import User
from src.get_conn import get_db
from typing import Annotated
from src.utils import create_access_token, verify_access_token
from src.api_models import UserCreate, LoginRequest, TokenResponse, LogoutResponse, UserResponse, UserRead
from jose import JWTError

router = APIRouter()
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")


@router.post("/token", response_model=TokenResponse)
# トークンの発行
async def get_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):

    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not user.check_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )
    if not user.is_active():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    access_token = create_access_token(data={"sub": user.email})

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/create-user", response_model=UserResponse)
# ユーザー登録
async def create_user(
    token: str = Depends(oauth2_scheme),
    form_data: UserCreate = None,
    db: Session = Depends(get_db),
):
    try:
        payload = verify_access_token(token)

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")

        existing_user = db.query(User).filter(
            User.email == form_data.name).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists",
            )

        result = User.create_user(db=db, form_data=form_data)

        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
# ログイン
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not user.check_password(request.password):
        raise HTTPException(
            status_code=401, detail="Invalid email or password")
    if user.disabled:
        raise HTTPException(status_code=403, detail="User account is disabled")

    try:
        access_token = create_access_token(data={"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate access token: {str(e)}"
        )


@router.post("/logout", response_model=LogoutResponse)
# ログアウト
async def logout(token: str = Depends(oauth2_scheme)):
    return {"message": "User logged out successfully"}


@router.get("/user", response_model=UserRead)
# 自分の情報を取得
async def get_user_info(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = verify_access_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")

        email = payload.get("sub")
        user = User.get_user(db=db, email=email)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user.disabled:
            raise HTTPException(
                status_code=403, detail="User account is disabled")

        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user information: {str(e)}"
        )

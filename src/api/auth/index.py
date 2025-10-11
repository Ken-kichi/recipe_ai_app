from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, FastAPI
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.db_models import User
from src.get_conn import get_db
from typing import Annotated
from src.utils import create_access_token, verify_access_token
from src.api_models import UserCreate

# トークンの発行

router = APIRouter()


app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")


@router.post("/token")
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


@router.post("/create-user")
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
        new_user = User(
            name=form_data.name,
            email=form_data.email,
            disabled=False
        )
        new_user.set_password(form_data.password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "message": "User created successfully",
            "user_id": new_user.id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


# # ログイン
# # ログアウト
# # 自分の情報を取得

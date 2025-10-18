from fastapi.security import OAuth2PasswordBearer
from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.db_models import User, Image, Recipe
from src.get_conn import get_db
from src.utils import verify_access_token
from src.api_models import RecipeResponse, RecipeRead

router = APIRouter()
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")


@router.post("/create-recipe", response_model=RecipeResponse)
# レシピ生成
async def create_recipe(
    title: str,
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
            raise HTTPException(
                status_code=401, detail="User not found"
            )
        if user.disabled:
            raise HTTPException(
                status_code=403, detail="User account is disabled")

        recipe_result = Recipe.registry_recipe(
            title=title,
            user_id=user.id,
            db=db
        )
        image_result = Image.registry_image(
            recipe=recipe_result["content"],
            recipe_id=recipe_result["recipe_id"],
            db=db
        )

        return {
            "message": "Recipe and image created successfully",
            "recipe_id": recipe_result["recipe_id"],
            "image_url": image_result.image_url
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to registry Recipe: {str(e)}"
        )


@router.get("/user-recipes", response_model=list[RecipeRead])
async def get_user_recipes(
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
            raise HTTPException(
                status_code=401, detail="User not found"
            )
        if user.disabled:
            raise HTTPException(
                status_code=403, detail="User account is disabled")

        recipes = Recipe.get_recipes_by_user(user_id=user.id, db=db)
        # Recipe.get_recipes_by_user returns a list of dicts already
        # so return it directly to avoid attribute access on dicts
        return recipes

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve recipes: {str(e)}"
        )
# ログインユーザーのレシピ一覧
# レシピ詳細
# レシピ編集
# レシピ削除

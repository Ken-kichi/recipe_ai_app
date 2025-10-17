from fastapi import FastAPI
from src.api.auth.index import router as auth_router
from src.api.recipe.index import router as recipe_router
app = FastAPI()

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

app.include_router(recipe_router, prefix="/api/recipe", tags=["recipe"])

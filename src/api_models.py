from pydantic import BaseModel
from datetime import datetime

# ------------------------------
# User Models
# ------------------------------


class UserBase(BaseModel):
    name: str
    email: str
    disabled: bool | None = None


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

# ------------------------------
# Ingredient Models
# ------------------------------


class IngredientBase(BaseModel):
    name: str
    unit: str
    calories: float | None = 0
    protein: float | None = 0
    fat: float | None = 0
    carbohydrates: float | None = 0


class IngredientRead(IngredientBase):
    id: int

    class Config:
        orm_mode = True

# ------------------------------
# RecipeIngredient Models
# ------------------------------


class RecipeIngredientBase(BaseModel):
    ingredient_id: int
    quantity: float


class RecipeIngredientRead(BaseModel):
    id: int
    quantity: float
    ingredient: IngredientRead

    class Config:
        orm_mode = True

# ------------------------------
# Step Models
# ------------------------------


class StepBase(BaseModel):
    step_number: int
    instruction: str


class StepRead(StepBase):
    id: int

    class Config:
        orm_mode = True

# ------------------------------
# Image Models
# ------------------------------


class ImageBase(BaseModel):
    image_url: str
    is_regenerated: bool | None = False


class ImageRead(ImageBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

# ------------------------------
# Nutrition Models
# ------------------------------


class NutritionBase(BaseModel):
    calories: float | None = 0
    protein: float | None = 0
    fat: float | None = 0
    carbohydrates: float | None = 0
    fiber: float | None = 0
    salt: float | None = 0


class NutritionRead(NutritionBase):
    id: int

    class Config:
        orm_mode = True

# ------------------------------
# Recipe Models
# ------------------------------


class RecipeBase(BaseModel):
    title: str
    markdown_content: str
    nutrition_satisfied: bool | None = False


class RecipeRead(RecipeBase):
    id: int
    created_at: datetime
    steps: list[StepRead] = []
    recipe_ingredients: list[RecipeIngredientRead] = []
    images: list[ImageRead] = []
    nutrition: NutritionRead | None = None

    class Config:
        orm_mode = True

# ------------------------------
# StripePlan Models
# ------------------------------


class StripePlanBase(BaseModel):
    stripe_plan_id: str
    name: str
    price: float
    interval: str


class StripePlanRead(StripePlanBase):
    id: int

    class Config:
        orm_mode = True

# ------------------------------
# Subscription Models
# ------------------------------


class SubscriptionBase(BaseModel):
    stripe_plan_id: int
    status: str
    start_date: datetime
    end_date: datetime | None = None


class SubscriptionRead(SubscriptionBase):
    id: int
    stripe_plan: StripePlanRead | None = None

    class Config:
        orm_mode = True

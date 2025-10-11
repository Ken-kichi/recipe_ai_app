from pydantic import BaseModel, Field
from datetime import datetime

# ------------------------------
# User Models
# ------------------------------


class UserBase(BaseModel):
    name: str = Field(..., example="Alice")
    email: str = Field(..., example="alice@example.com")
    disabled: bool | None = Field(..., example="False")


class UserCreate(UserBase):
    password: str = Field(..., example="hashed_pw_123")


class UserRead(UserBase):
    id: int = Field(..., example="1")
    created_at: datetime = Field(..., example=datetime.utcnow())

    class Config:
        orm_mode = True

# ------------------------------
# Ingredient Models
# ------------------------------


class IngredientBase(BaseModel):
    name: str = Field(..., example="Tomato")
    unit: str = Field(..., example="g")
    calories: float | None = Field(18.0, example=18.0)
    protein: float | None = Field(0.9, example=0.9)
    fat: float | None = Field(0.2, example=0.2)
    carbohydrates: float | None = Field(3.9, example=3.9)


class IngredientRead(IngredientBase):
    id: int = Field(..., example=1)

    class Config:
        orm_mode = True

# ------------------------------
# RecipeIngredient Models
# ------------------------------


class RecipeIngredientBase(BaseModel):
    ingredient_id: int = Field(..., example=1)
    quantity: float = Field(..., example=100.0)


class RecipeIngredientRead(BaseModel):
    id: int = Field(..., example=1)
    quantity: float = Field(..., example=100.0)
    ingredient: IngredientRead = Field(
        ..., example={"id": 1, "name": "Tomato", "unit": "g", "calories": 18.0}
    )

    class Config:
        orm_mode = True

# ------------------------------
# Step Models
# ------------------------------


class StepBase(BaseModel):
    step_number: int = Field(..., example=1)
    instruction: str = Field(..., example="Cut the tomato into small pieces.")


class StepRead(StepBase):
    id: int = Field(..., example=1)

    class Config:
        orm_mode = True


# ------------------------------
# Image Models
# ------------------------------


class ImageBase(BaseModel):
    image_url: str = Field(..., example="https://example.com/image1.jpg")
    is_regenerated: bool | None = Field(False, example=False)


class ImageRead(ImageBase):
    id: int = Field(..., example=1)
    created_at: datetime = Field(..., example="2025-10-11T12:34:56Z")

    class Config:
        orm_mode = True

# ------------------------------
# Nutrition Models
# ------------------------------


class NutritionBase(BaseModel):
    calories: float | None = Field(450.0, example=450.0)
    protein: float | None = Field(25.0, example=25.0)
    fat: float | None = Field(15.0, example=15.0)
    carbohydrates: float | None = Field(55.0, example=55.0)
    fiber: float | None = Field(5.0, example=5.0)
    salt: float | None = Field(1.2, example=1.2)


class NutritionRead(NutritionBase):
    id: int = Field(..., example=1)

    class Config:
        orm_mode = True

# ------------------------------
# Recipe Models
# ------------------------------


class RecipeBase(BaseModel):
    title: str = Field(..., example="Tomato Salad")
    markdown_content: str = Field(...,
                                  example="### How to make a simple tomato salad...")
    nutrition_satisfied: bool | None = Field(False, example=True)


class RecipeRead(RecipeBase):
    id: int = Field(..., example=1)
    created_at: datetime = Field(..., example="2025-10-11T12:34:56Z")
    steps: list[StepRead] = Field(
        default_factory=list,
        example=[{"id": 1, "step_number": 1, "instruction": "Cut tomatoes."}],
    )
    recipe_ingredients: list[RecipeIngredientRead] = Field(
        default_factory=list,
        example=[{"id": 1, "quantity": 100, "ingredient": {
            "id": 1, "name": "Tomato", "unit": "g"}}],
    )
    images: list[ImageRead] = Field(
        default_factory=list,
        example=[{"id": 1, "image_url": "https://example.com/image1.jpg"}],
    )
    nutrition: NutritionRead | None = Field(
        None,
        example={"id": 1, "calories": 450, "protein": 25,
                 "fat": 15, "carbohydrates": 55},
    )

    class Config:
        orm_mode = True

# ------------------------------
# StripePlan Models
# ------------------------------


class StripePlanBase(BaseModel):
    stripe_plan_id: str = Field(..., example="plan_12345")
    name: str = Field(..., example="Pro Plan")
    price: float = Field(..., example=9.99)
    interval: str = Field(..., example="month")


class StripePlanRead(StripePlanBase):
    id: int = Field(..., example=1)

    class Config:
        orm_mode = True

# ------------------------------
# Subscription Models
# ------------------------------


class SubscriptionBase(BaseModel):
    stripe_plan_id: int = Field(..., example=1)
    status: str = Field(..., example="active")
    start_date: datetime = Field(..., example="2025-10-01T00:00:00Z")
    end_date: datetime | None = Field(None, example="2025-11-01T00:00:00Z")


class SubscriptionRead(SubscriptionBase):
    id: int = Field(..., example=1)
    stripe_plan: StripePlanRead | None = Field(
        None,
        example={"id": 1, "name": "Pro Plan",
                 "price": 9.99, "interval": "month"},
    )

    class Config:
        orm_mode = True

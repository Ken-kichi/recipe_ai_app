from pydantic import BaseModel, Field
from datetime import datetime

# ------------------------------
# Login Models
# ------------------------------


class LoginRequest(BaseModel):
    email: str = Field(..., example="alice@example.com")
    password: str = Field(..., example="hashed_pw_123")


class TokenResponse(BaseModel):
    access_token: str = Field(...,
                              example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    token_type: str = Field(default="bearer")

# ------------------------------
# Logout Models
# ------------------------------


class LogoutResponse(BaseModel):
    message: str = Field(..., example="User logged out successfully")


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


class UserResponse(BaseModel):
    message: str = Field(..., example="User created successfully")
    user_id: int = Field(..., example="1")


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
# Recipe Models
# ------------------------------


class RecipeResponse(BaseModel):
    message: str = Field(..., example="Recipe created successfully")
    recipe_id: int = Field(..., example="1")


class ImageInfo(BaseModel):
    id: int
    image_url: str
    is_regenerated: bool
    created_at: datetime

    class Config:
        orm_mode = True


class RecipeBase(BaseModel):
    title: str = Field(..., example="Tomato Salad")


class RecipeRead(RecipeBase):
    id: int = Field(..., example=1)
    markdown_content: str = Field(...,
                                  example="### How to make a simple tomato salad...")
    user: str = Field(..., example="Alice")
    created_at: datetime = Field(..., example="2025-10-11T12:34:56Z")
    images: list[ImageRead] = Field(
        default_factory=list,
        example=[{"id": 1, "image_url": "https://example.com/image1.jpg"}],
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

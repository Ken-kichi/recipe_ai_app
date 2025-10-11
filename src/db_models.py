from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
)
from sqlalchemy.orm import relationship, declarative_base, Session
from werkzeug.security import generate_password_hash, check_password_hash
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    disabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    recipes = relationship("Recipe", back_populates="user",
                           cascade="all, delete-orphan")
    subscriptions = relationship(
        "Subscription", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        """Store the password as a hash"""
        self.password_hash = generate_password_hash(password)

    def check_passowrd(self, password: str) -> bool:
        """Verify the input password against the hash"""
        return check_password_hash(self.password_hash, password)

    def is_active(self) -> bool:
        """Whether the user is active"""
        return not self.disabled

    def current_subscription(self):
        """Return currently active subscriptions (with expiration check)"""
        active_subs = [
            sub for sub in self.subscriptions
            if sub.status == "active" and (sub.end_date is None or sub.end_date > datetime.utcnow())
        ]
        return active_subs[0] if active_subs else None

    def __repr__(self):
        return f"<User id={self.id} name={self.name} email={self.email}>"


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    markdown_content = Column(Text, nullable=False)
    nutrition_satisfied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="recipes")
    steps = relationship("Step", back_populates="recipe",
                         cascade="all, delete-orphan")
    recipe_ingredients = relationship(
        "RecipeIngredient",
        back_populates="recipe",
        cascade="all, delete-orphan"
    )
    images = relationship(
        "Image",
        back_populates="recipe",
        cascade="all, delete-orphan"
    )
    nutrition = relationship(
        "Nutrition",
        back_populates="recipe",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def calculate_nutrition(self, db: Session):
        """
        Calculate the total nutrients from the ingredients included in the recipe and save them to the Nutrition table.
        """
        total_calories = 0
        total_protein = 0
        total_fat = 0
        total_carbs = 0

        for ri in self.recipe_ingredients:
            ingredient = ri.ingredient
            quantity = ri.quantity
            total_calories += ingredient.calories*quantity/100
            total_protein += ingredient.protein*quantity/100
            total_fat += ingredient.fat*quantity/100

        if self.nutrition is None:
            from src.db_models import Nutrition
            self.nutrition = Nutrition(
                recipe_id=self.id,
                calories=total_calories,
                protein=total_protein,
                fat=total_fat
            )
        else:
            self.nutrition.calories = total_calories
            self.nutrition.protein = total_protein
            self.nutrition.fat = total_fat

        db.add(self)
        db.commit()
        db.refresh(self)

    async def generate_description(self, openai_api_key: str):
        """
        Generate descriptions for recipes using AI based on their titles.
        """
        llm = ChatOpenAI(model="gpt-5-mini", openai_api_key=openai_api_key)
        template = """
        Please generate a description for the following dish within 80 characters: {title}
        """
        prompt = PromptTemplate.from_template(
            template=template
        )
        chain = prompt | llm
        result = await chain.invoke({
            "title": self.title
        })
        return result.content

    def check_nutrition_balance(self):
        """
        Determine whether the nutritional balance meets the daily standard.
        """
        if not self.nutrition:
            return False

        return (
            1800 <= self.nutrition.calories <= 2200 and
            50 <= self.nutrition.protein <= 70 and
            40 <= self.nutrition.fat <= 70
        )


class Step(Base):
    __tablename__ = "steps"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey(
        "recipes.id", ondelete="CASCADE"), nullable=False)
    step_number = Column(Integer, nullable=False)
    instruction = Column(Text, nullable=False)

    # Relationships
    recipe = relationship("Recipe", back_populates="steps")

    def to_dict(self):
        """
        Converts step information into a dictionary format and returns it.
        Useful for API responses and JSON conversion.
        """
        return {
            "id": self.id,
            "recipe_id": self.recipe_id,
            "step_number": self.step_number,
            "instruction": self.instruction,
        }

    def short_instruction(self, length: int = 50):
        """
        A method to shorten long procedure statements and display a preview.
        """
        return (self.instruction[:length] + "...") if len(self.instruction) > length else self.instruction

    def __repr__(self):
        return f"<Step #{self.step_number}: {self.short_instruction(30)}>"


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    unit = Column(String, nullable=False)
    calories = Column(Float)
    protein = Column(Float)
    fat = Column(Float)
    carbohydrates = Column(Float)

    # Relationships
    recipe_ingredients = relationship(
        "RecipeIngredient", back_populates="ingredient", cascade="all, delete-orphan")

    def to_dict(self):
        """
        Convert ingredient information into dictionary format and return it (for use in API responses, etc.)
        """
        return {
            "id": self.id,
            "name": self.name,
            "unit": self.unit,
            "calories": self.calories,
            "protein": self.protein,
            "fat": self.fat,
            "carbohydrates": self.carbohydrates,
        }

    def calculation_nutrition(self, quantity: float):
        """
       Calculate nutritional value based on the specified quantity.
       Example: quantity=2 → Returns nutritional values for 2 units.
        """
        return {
            "calories": (self.calories or 0) * quantity,
            "protein": (self.protein or 0) * quantity,
            "fat": (self.fat or 0) * quantity,
            "carbohydrates": (self.carbohydrates or 0) * quantity,
        }

    def __repr__(self):
        return f"<Ingredient(name={self.name}, unit={self.unit}, kcal={self.calories})>"


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey(
        "recipes.id", ondelete="CASCADE"), nullable=False)
    ingredient_id = Column(Integer, ForeignKey(
        "ingredients.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Float, nullable=False)

    # Relationships
    recipe = relationship("Recipe", back_populates="recipe_ingredients")
    ingredient = relationship(
        "Ingredient", back_populates="recipe_ingredients")

    def total_nutrition(self):
        """
        Calculate the total nutritional value within the recipe based on the amount of this ingredient used.
        Calculated as: Nutritional value of the Ingredient model × quantity.
        """
        if not self.ingredient:
            return {"calories": 0, "protein": 0, "fat": 0, "carbohydrates": 0}

        return {
            "calories": (self.ingredient.calories or 0) * self.quantity,
            "protein": (self.ingredient.protein or 0) * self.quantity,
            "fat": (self.ingredient.fat or 0) * self.quantity,
            "carbohydrates": (self.ingredient.carbohydrates or 0) * self.quantity,
        }

    def to_dict(self, include_nutrition: bool = False):
        """
        Convert to a dictionary format that is easy to handle in API responses, etc.
        Include nutrition information when `include_nutrition=True`.
        """
        data = {
            "id": self.id,
            "recipe_id": self.recipe_id,
            "ingredient_id": self.ingredient_id,
            "ingredient_name": self.ingredient.name if self.ingredient else None,
            "quantity": self.quantity,
            "unit": self.ingredient.unit if self.ingredient else None,
        }

        if include_nutrition:
            data.update(self.total_nutrition())

        return data

    def __repr__(self):
        ing_name = self.ingredient.name if self.ingredient else "Unknown"
        return f"<RecipeIngredient(ingredient={ing_name}, qty={self.quantity}{self.ingredient.unit if self.ingredient else ''})>"


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey(
        "recipes.id", ondelete="CASCADE"), nullable=False)
    image_url = Column(String, nullable=False)
    is_regenerated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    recipe = relationship("Recipe", back_populates="images")

    def mark_regenerated(self):
        """
        Update the flag when the image is regenerated.
        """
        self.is_regenerated = True

    def filename(self):
        """
        Extract the filename from the URL
        """
        return self.image_url.split("/")[-1]

    def to_dict(self):
        """
        Return in dictionary format for API responses
        """
        return {
            "id": self.id,
            "recipe_id": self.recipe_id,
            "image_url": self.image_url,
            "is_regenerated": self.is_regenerated,
            "created_at": self.created_at.isoformat(),
            "filename": self.filename()
        }

    def __repr__(self):
        return f"<Image(id={self.id}, url={self.image_url}, regenerated={self.is_regenerated})>"


class Nutrition(Base):
    __tablename__ = "nutritions"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey(
        "recipes.id", ondelete="CASCADE"), nullable=False)
    calories = Column(Float)
    protein = Column(Float)
    fat = Column(Float)
    carbohydrates = Column(Float)
    fiber = Column(Float)
    salt = Column(Float)

    # Relationships
    recipe = relationship("Recipe", back_populates="nutrition")

    def total_calories(self):
        """
        Return total calories
        """
        return self.calories or 0

    def pfc_ratio(self):
        """
        Calculates and returns the calorie ratio of protein, fat, and carbohydrates.
        Example: {‘protein’: 30, ‘fat’: 25, ‘carbohydrates’: 45} (%)
        """
        protein_cal = (self.protein or 0) * 4
        fat_cal = (self.fat or 0) * 9
        carb_cal = (self.carbohydrates or 0) * 4

        total = protein_cal + fat_cal + carb_cal
        if total == 0:
            return {"protein": 0, "fat": 0, "carbohydrates": 0}

        return {
            "protein": round(protein_cal / total * 100, 1),
            "fat": round(fat_cal / total * 100, 1),
            "carbohydrates": round(carb_cal / total * 100, 1),
        }

    def to_dict(self):
        """
        Return in dictionary format for API responses
        """
        return {
            "calories": self.calories,
            "protein": self.protein,
            "fat": self.fat,
            "carbohydrates": self.carbohydrates,
            "fiber": self.fiber,
            "salt": self.salt,
            "pfc_ratio": self.pfc_ratio()
        }

    def __repr__(self):
        return (f"<Nutrition(calories={self.calories}, protein={self.protein}, "
                f"fat={self.fat}, carbs={self.carbohydrates})>")


class StripePlan(Base):
    __tablename__ = "stripe_plans"

    id = Column(Integer, primary_key=True, index=True)
    stripe_plan_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    interval = Column(String, nullable=False)

    # Relationships
    subscriptions = relationship(
        "Subscription", back_populates="stripe_plan", cascade="all, delete-orphan")

    def display_price(self):
        """
            Return the price and billing interval as a string.
            Example: “$10 / month”
            """
        return f"${self.price} / {self.interval}"

    def monthly_price(self):
        """
        Return the monthly equivalent price.
        For annual payments, divide by 12.
        """
        if self.interval.lower() == "yearly":
            return round(self.price / 12, 2)
        return self.price

    def to_dict(self):
        """
        Return in dictionary format for API responses
        """
        return {
            "id": self.id,
            "stripe_plan_id": self.stripe_plan_id,
            "name": self.name,
            "price": self.price,
            "interval": self.interval,
            "display_price": self.display_price(),
            "monthly_price": self.monthly_price(),
        }

    def __repr__(self):
        return f"<StripePlan(name={self.name}, price={self.price}, interval={self.interval})>"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False)
    stripe_plan_id = Column(Integer, ForeignKey(
        "stripe_plans.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    stripe_plan = relationship("StripePlan", back_populates="subscriptions")

    def is_active(self):
        """
        Check if your current subscription is active
        """
        now = datetime.utcnow()
        if self.status.lower() != "active":
            return False
        if self.end_date and now > self.end_date:
            return False
        return True

    def days_remaining(self):
        """
        Return the remaining days of the subscription
        """
        if not self.end_date:
            return None
        now = datetime.utcnow()
        remaining = (self.end_date - now).days
        return max(remaining, 0)

    def to_dict(self):
        """
        Return in dictionary format for API responses
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "stripe_plan_id": self.stripe_plan_id,
            "plan_name": self.stripe_plan.name if self.stripe_plan else None,
            "status": self.status,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "is_active": self.is_active(),
            "days_remaining": self.days_remaining(),
        }

    def __repr__(self):
        return f"<Subscription(user_id={self.user_id}, plan={self.stripe_plan.name if self.stripe_plan else 'Unknown'}, status={self.status})>"

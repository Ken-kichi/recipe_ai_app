from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
)
from sqlalchemy.orm import relationship, declarative_base, Session
from werkzeug.security import generate_password_hash, check_password_hash
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import requests

# .env をロード
load_dotenv()
Base = declarative_base()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")


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

    # ------------------------------
    # 全ユーザー取得
    # ------------------------------
    @staticmethod
    def get_users(db: Session):
        return db.query(User).all()

    # ------------------------------
    # ユーザー取得
    # ------------------------------
    @staticmethod
    def get_user(db: Session, email: str):
        user = db.query(User).filter(User.email == email).first()
        if user:
            return user
        return None

    # ------------------------------
    # 新規ユーザー作成
    # ------------------------------
    @staticmethod
    def create_user(db: Session, form_data):
        new_user = User(
            name=form_data.name,
            email=form_data.email,  # username を email として利用
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

    # ------------------------------
    # ユーザー削除
    # ------------------------------
    @staticmethod
    def delete_user(db: Session, form_data):
        try:
            user = db.query(User).filter(User.email == form_data.email).first()
            if user and user.check_password(form_data.password):
                db.delete(user)
                db.commit()
                return {"message": "User deleted successfully"}
            else:
                raise HTTPException(
                    status_code=404,
                    detail="User not found or incorrect password"
                )

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Failed to create user: {e}"
            )

    # ------------------------------
    # パスワード設定・確認
    # ------------------------------
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # ------------------------------
    # その他ユーティリティ
    # ------------------------------
    def is_active(self) -> bool:
        return not self.disabled

    def current_subscription(self):
        active_subs = []
        for sub in self.subscriptions:
            if sub.status == "active" and (sub.end_date is None or sub.end_date > datetime.utcnow()):
                active_subs.append(sub)

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
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="recipes")

    images = relationship(
        "Image",
        back_populates="recipe",
        cascade="all, delete-orphan"
    )

    @staticmethod
    def generate_recipe(title: str, db: Session) -> str:
        # レシピ生成
        endpoint = os.getenv("AZURE_ENDPOINT")
        deployment = os.getenv("AZURE_DEPLOYMENT")

        subscription_key = os.getenv("AZURE_SUBSCRIPTION_KEY")
        api_version = os.getenv("AZURE_API_VERSION")

        client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=endpoint,
            api_key=subscription_key,
        )

        prompt = f"""
            あなたは栄養士兼料理研究家です。
            家庭でも簡単に作れる、栄養バランスの良い料理を考えてください。
            以下の条件を満たすレシピを提案してください：
            - 3ステップで調理できる
            - 調味料は家庭にある基本的なもの（塩、醤油、砂糖、油など）
            - 1食分あたり、たんぱく質・炭水化物・野菜をバランスよく含む
            - 短時間で調理できる（20分以内）
            - 洗い物が少ない

            出力形式：
            ---
            料理名：
            材料：
            作り方：
            栄養ポイント：
            ---
            テーマ: {title}
        """

        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=16384
        )

        print(response)

        if not response.choices or len(response.choices) == 0:
            raise ValueError("Azure OpenAI response is empty")

        # ChatCompletionの場合はこちら
        text = response.choices[0].message.content
        if not text:
            raise ValueError("Generated text is empty")

        return text

    @staticmethod
    def registry_recipe(title: str, user_id: int, db: Session):
        # レシピ登録

        generated_recipe = Recipe.generate_recipe(title, db)

        new_recipe = Recipe(
            user_id=user_id,
            title=title,
            markdown_content=generated_recipe,
            created_at=datetime.utcnow(),
        )

        db.add(new_recipe)
        db.commit()
        db.refresh(new_recipe)

        return {
            "message": "Recipe created successfully",
            "recipe_id": new_recipe.id,
            "content": new_recipe.markdown_content
        }

    # ログインユーザーのレシピ一覧
    @staticmethod
    def get_recipes_by_user(db: Session, user_id: int) -> list[dict]:
        recipes = db.query(Recipe).filter(Recipe.user_id == user_id).all()
        return [
            {
                "id": recipe.id,
                "title": recipe.title,
                # pydantic model expects `markdown_content` field name
                "markdown_content": recipe.markdown_content,
                # include owner's name for `user` field expected by RecipeRead
                "user": recipe.user.name if recipe.user else None,
                "created_at": recipe.created_at.isoformat() if recipe.created_at else None,
                "images": [
                    {
                        "id": image.id,
                        "image_url": image.image_url,
                        "is_regenerated": image.is_regenerated,
                        "created_at": image.created_at.isoformat() if image.created_at else None,
                    }
                    for image in recipe.images
                ]
            }
            for recipe in recipes
        ]

    # レシピ詳細
    @staticmethod
    def get_recipe_by_id(db: Session, recipe_id: int) -> dict:
        recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if not recipe:
            return None
        return {
            "id": recipe.id,
            "title": recipe.title,
            # pydantic model expects `markdown_content` field name
            "markdown_content": recipe.markdown_content,
            # include owner's name for `user` field expected by RecipeRead
            "user": recipe.user.name if recipe.user else None,
            "created_at": recipe.created_at.isoformat() if recipe.created_at else None,
            "images": [
                {
                    "id": image.id,
                    "image_url": image.image_url,
                    "is_regenerated": image.is_regenerated,
                    "created_at": image.created_at.isoformat() if image.created_at else None,
                }
                for image in recipe.images
            ]
        }

    # レシピ編集
    # レシピ削除


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

    def generate_image(recipe: str, recipe_id: int, db: Session):
        """
        DALL·E 3 を使用して、レシピから料理の画像を生成し、
        生成したURLをデータベースに保存する関数。
        """
        api_key = os.getenv("AZURE_IMAGE_API_KEY")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        prompt = f"""
                あなたは料理のビジュアルアーティストです。
                以下のレシピの完成料理をリアルで美味しそうに描写してください。

                ---
                {recipe}
                ---

                出力形式: 写実的で明るい照明の料理写真風画像
                """

        data = {
            "model": "dall-e-3",
            "prompt": prompt,
            "size": "1024x1024",
            "style": "vivid",
            "quality": "standard",
            "n": 1
        }

        url = os.getenv("AZURE_IMAGE_API_URI")

        response = requests.post(url, headers=headers, json=data)

        result = response.json()
        image_url = result["data"][0]["url"]
        return image_url

    @staticmethod
    def registry_image(recipe: str, recipe_id: int, db: Session):

        image_url = Image.generate_image(recipe, recipe_id, db)
        new_image = Image(
            recipe_id=recipe_id,
            image_url=image_url
        )
        db.add(new_image)
        db.commit()
        db.refresh(new_image)

        return new_image

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

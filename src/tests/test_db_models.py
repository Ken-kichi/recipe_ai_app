import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db_models import (
    Base,
    User,
    Recipe,
    Step,
    Ingredient,
    RecipeIngredient,
    StripePlan,
    Subscription,
    Nutrition,
    Image
)

# ------------------------------
# テスト用DBセットアップ
# ------------------------------


@pytest.fixture(scope="function")
def db_session():
    # メモリ内SQLite DB
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)

# ------------------------------
# Userモデルの基本テスト
# ------------------------------


def test_user_active_flag(db_session):
    user = User(name="Alice", email="alice@example.com",
                disabled=False, password_hash="dummy")
    db_session.add(user)
    db_session.commit()

    assert user.is_active() is True

    # 無効化
    user.disabled = True
    assert user.is_active() is False

# ------------------------------
# Passwordハッシュのテスト
# ------------------------------


def test_user_password_methods(db_session):
    user = User(name="Bob", email="bob@example.com",
                disabled=False, password_hash="")
    user.set_password("secret123")
    db_session.add(user)
    db_session.commit()

    # 正しいパスワード
    assert user.check_passowrd("secret123") is True
    # 間違ったパスワード
    assert user.check_passowrd("wrongpass") is False

# ------------------------------
# current_subscriptionメソッドのテスト
# ------------------------------


def test_current_subscription(db_session):
    user = User(name="Charlie", email="charlie@example.com",
                disabled=False, password_hash="dummy")
    db_session.add(user)
    db_session.commit()

    # StripePlan作成
    plan = StripePlan(stripe_plan_id="plan001", name="Pro",
                      price=100, interval="monthly")
    db_session.add(plan)
    db_session.commit()

    # 有効なサブスクリプション
    sub_active = Subscription(
        user=user,
        stripe_plan=plan,
        status="active",
        start_date=datetime.utcnow() - timedelta(days=1),
        end_date=datetime.utcnow() + timedelta(days=30)
    )
    # 無効なサブスクリプション
    sub_inactive = Subscription(
        user=user,
        stripe_plan=plan,
        status="inactive",
        start_date=datetime.utcnow() - timedelta(days=10),
        end_date=datetime.utcnow() - timedelta(days=5)
    )

    db_session.add_all([sub_active, sub_inactive])
    db_session.commit()

    current = user.current_subscription()
    assert current is not None
    assert current.status == "active"
    assert current.user_id == user.id

# ------------------------------
# __repr__のテスト
# ------------------------------


def test_user_repr(db_session):
    user = User(name="Dana", email="dana@example.com",
                disabled=False, password_hash="dummy")
    db_session.add(user)
    db_session.commit()

    rep = repr(user)
    assert "Dana" in rep
    assert "dana@example.com" in rep

# ------------------------------
# Recipe.calculate_nutrition のテスト
# ------------------------------


def test_calculate_nutrition(db_session):
    # ユーザー作成
    user = User(name="Alice", email="alice@example.com", password_hash="dummy")
    db_session.add(user)
    db_session.commit()

    # 食材作成
    ing1 = Ingredient(
        name="Banana",
        unit="g",
        calories=89,
        protein=1.1,
        fat=0.3,
        carbohydrates=23
    )
    ing2 = Ingredient(
        name="Egg",
        unit="g",
        calories=155,
        protein=13,
        fat=11,
        carbohydrates=1.1
    )
    db_session.add_all([ing1, ing2])
    db_session.commit()

    # レシピ作成
    recipe = Recipe(user_id=user.id, title="Banana Omelette",
                    markdown_content="Mix and cook")
    db_session.add(recipe)
    db_session.commit()

    # RecipeIngredient 作成
    ri1 = RecipeIngredient(recipe=recipe, ingredient=ing1, quantity=100)
    ri2 = RecipeIngredient(recipe=recipe, ingredient=ing2, quantity=50)
    db_session.add_all([ri1, ri2])
    db_session.commit()

    # 栄養計算
    recipe.calculate_nutrition(db_session)

    assert recipe.nutrition is not None
    # 計算の確認
    expected_calories = 89*100/100 + 155*50/100
    expected_protein = 1.1*100/100 + 13*50/100
    expected_fat = 0.3*100/100 + 11*50/100

    assert abs(recipe.nutrition.calories - expected_calories) < 0.01
    assert abs(recipe.nutrition.protein - expected_protein) < 0.01
    assert abs(recipe.nutrition.fat - expected_fat) < 0.01

# ------------------------------
# Recipe.check_nutrition_balance のテスト
# ------------------------------


def test_check_nutrition_balance(db_session):
    # ユーザー作成
    user = User(name="Bob", email="bob@example.com", password_hash="dummy")
    db_session.add(user)
    db_session.commit()

    # レシピ作成
    recipe = Recipe(user_id=user.id, title="Test Dish",
                    markdown_content="Step1")
    db_session.add(recipe)
    db_session.commit()

    # 栄養情報なしの場合は False
    assert recipe.check_nutrition_balance() is False

    # 栄養情報を追加
    nutrition = Nutrition(
        recipe=recipe,
        calories=2000,
        protein=60,
        fat=50,
        carbohydrates=250
    )
    db_session.add(nutrition)
    db_session.commit()

    assert recipe.check_nutrition_balance() is True

    # 栄養が不足の場合
    nutrition.protein = 30
    db_session.commit()
    assert recipe.check_nutrition_balance() is False


def test_step_to_dict_and_short_instruction(db_session):
    # ユーザー作成
    user = User(name="Alice", email="alice@example.com", password_hash="dummy")
    db_session.add(user)
    db_session.commit()

    # レシピ作成
    recipe = Recipe(user_id=user.id, title="Sample Dish",
                    markdown_content="Mix ingredients")
    db_session.add(recipe)
    db_session.commit()

    # Step 作成
    instruction_text = "Step 1: Chop the onions finely and sauté them until golden brown."
    step = Step(recipe_id=recipe.id, step_number=1,
                instruction=instruction_text)
    db_session.add(step)
    db_session.commit()

    # to_dict の確認
    step_dict = step.to_dict()
    assert step_dict["id"] == step.id
    assert step_dict["recipe_id"] == recipe.id
    assert step_dict["step_number"] == 1
    assert step_dict["instruction"] == instruction_text

    # short_instruction の確認
    short = step.short_instruction(length=20)
    assert short == instruction_text[:20] + "..."

    # instruction が短い場合はそのまま
    short_full = step.short_instruction(length=100)
    assert short_full == instruction_text


def test_ingredient_to_dict(db_session):
    ingredient = Ingredient(
        name="Banana",
        unit="g",
        calories=89,
        protein=1.1,
        fat=0.3,
        carbohydrates=23
    )
    db_session.add(ingredient)
    db_session.commit()

    d = ingredient.to_dict()
    assert d["name"] == "Banana"
    assert d["unit"] == "g"
    assert d["calories"] == 89
    assert d["protein"] == 1.1
    assert d["fat"] == 0.3
    assert d["carbohydrates"] == 23


def test_ingredient_calculation_nutrition(db_session):
    ingredient = Ingredient(
        name="Banana",
        unit="g",
        calories=89,
        protein=1.1,
        fat=0.3,
        carbohydrates=23
    )
    db_session.add(ingredient)
    db_session.commit()

    # quantity=2 units
    nut = ingredient.calculation_nutrition(quantity=2)
    assert nut["calories"] == 178
    assert nut["protein"] == 2.2
    assert nut["fat"] == 0.6
    assert nut["carbohydrates"] == 46

    # quantity=0 → all zeros
    nut_zero = ingredient.calculation_nutrition(quantity=0)
    assert nut_zero["calories"] == 0
    assert nut_zero["protein"] == 0
    assert nut_zero["fat"] == 0
    assert nut_zero["carbohydrates"] == 0


def test_total_nutrition(db_session):
    ingredient = Ingredient(
        name="Chicken Breast",
        unit="g",
        calories=165,
        protein=31,
        fat=3.6,
        carbohydrates=0
    )
    db_session.add(ingredient)
    db_session.commit()

    recipe_ingredient = RecipeIngredient(
        recipe_id=1,
        ingredient_id=ingredient.id,
        quantity=200,
        ingredient=ingredient
    )

    nut = recipe_ingredient.total_nutrition()
    # 200gなので栄養素は2倍
    assert nut["calories"] == 33000.0
    assert nut["protein"] == 6200.0
    assert nut["fat"] == 720.0
    assert nut["carbohydrates"] == 0


def test_to_dict(db_session):
    ingredient = Ingredient(
        name="Chicken Breast",
        unit="g",
        calories=165,
        protein=31,
        fat=3.6,
        carbohydrates=0
    )
    db_session.add(ingredient)
    db_session.commit()

    recipe_ingredient = RecipeIngredient(
        recipe_id=1,
        ingredient_id=ingredient.id,
        quantity=200,
        ingredient=ingredient
    )

    d = recipe_ingredient.to_dict(include_nutrition=True)
    assert d["ingredient_name"] == "Chicken Breast"
    assert d["quantity"] == 200
    assert d["unit"] == "g"
    assert d["calories"] == 330
    assert d["protein"] == 62
    assert d["fat"] == 7.2
    assert d["carbohydrates"] == 0


def test_mark_regenerated(db_session):
    img = Image(recipe_id=1, image_url="http://example.com/pic.jpg")
    db_session.add(img)
    db_session.commit()

    assert img.is_regenerated == False
    img.mark_regenerated()
    assert img.is_regenerated == True


def test_filename(db_session):
    img = Image(recipe_id=1, image_url="http://example.com/images/photo.png")
    db_session.add(img)
    db_session.commit()

    assert img.filename() == "photo.png"


def test_to_dict(db_session):
    now = datetime.utcnow()
    img = Image(
        recipe_id=1, image_url="http://example.com/pic.jpg", created_at=now)
    db_session.add(img)
    db_session.commit()

    d = img.to_dict()
    assert d["recipe_id"] == 1
    assert d["image_url"] == "http://example.com/pic.jpg"
    assert d["is_regenerated"] == False
    assert d["filename"] == "pic.jpg"
    assert d["created_at"] == now.isoformat()


def test_total_calories(db_session):
    nut = Nutrition(recipe_id=1, calories=500)
    db_session.add(nut)
    db_session.commit()

    assert nut.total_calories() == 500


def test_pfc_ratio(db_session):
    nut = Nutrition(recipe_id=1, protein=50, fat=30, carbohydrates=120)
    db_session.add(nut)
    db_session.commit()

    ratio = nut.pfc_ratio()
    total_percentage = sum(ratio.values())
    assert abs(total_percentage - 100) < 0.1  # 合計がほぼ100%
    assert all(k in ratio for k in ["protein", "fat", "carbohydrates"])


def test_pfc_ratio_zero(db_session):
    nut = Nutrition(recipe_id=1, protein=0, fat=0, carbohydrates=0)
    db_session.add(nut)
    db_session.commit()

    ratio = nut.pfc_ratio()
    assert ratio == {"protein": 0, "fat": 0, "carbohydrates": 0}


def test_to_dict(db_session):
    nut = Nutrition(
        recipe_id=1,
        calories=500,
        protein=50,
        fat=30,
        carbohydrates=120,
        fiber=10,
        salt=2
    )
    db_session.add(nut)
    db_session.commit()

    d = nut.to_dict()
    assert d["calories"] == 500
    assert d["protein"] == 50
    assert d["fat"] == 30
    assert d["carbohydrates"] == 120
    assert d["fiber"] == 10
    assert d["salt"] == 2
    assert "pfc_ratio" in d


def test_display_price(db_session):
    plan = StripePlan(
        stripe_plan_id="plan_001",
        name="Basic",
        price=10,
        interval="monthly"
    )
    db_session.add(plan)
    db_session.commit()

    assert plan.display_price() == "$10.0 / monthly"


def test_monthly_price_monthly(db_session):
    plan = StripePlan(
        stripe_plan_id="plan_002",
        name="Pro",
        price=20,
        interval="monthly"
    )
    db_session.add(plan)
    db_session.commit()

    assert plan.monthly_price() == 20


def test_monthly_price_yearly(db_session):
    plan = StripePlan(stripe_plan_id="plan_003",
                      name="Annual", price=120, interval="yearly")
    db_session.add(plan)
    db_session.commit()

    assert plan.monthly_price() == 10  # 120 / 12


def test_to_dict(db_session):
    plan = StripePlan(stripe_plan_id="plan_004",
                      name="Premium", price=30, interval="monthly")
    db_session.add(plan)
    db_session.commit()

    d = plan.to_dict()
    assert d["id"] == plan.id
    assert d["stripe_plan_id"] == "plan_004"
    assert d["name"] == "Premium"
    assert d["price"] == 30
    assert d["interval"] == "monthly"
    assert d["display_price"] == "$30 / monthly"
    assert d["monthly_price"] == 30


@pytest.fixture
def stripe_plan(db_session):
    plan = StripePlan(stripe_plan_id="plan_001", name="Basic",
                      price=10, interval="monthly")
    db_session.add(plan)
    db_session.commit()
    return plan


def test_is_active_true(db_session, stripe_plan):
    now = datetime.utcnow()
    sub = Subscription(
        user_id=1,
        stripe_plan_id=stripe_plan.id,
        status="active",
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=5)
    )
    db_session.add(sub)
    db_session.commit()
    assert sub.is_active() is True


def test_is_active_false_status(db_session, stripe_plan):
    now = datetime.utcnow()
    sub = Subscription(
        user_id=1,
        stripe_plan_id=stripe_plan.id,
        status="inactive",
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=5)
    )
    db_session.add(sub)
    db_session.commit()
    assert sub.is_active() is False


def test_is_active_false_expired(db_session, stripe_plan):
    now = datetime.utcnow()
    sub = Subscription(
        user_id=1,
        stripe_plan_id=stripe_plan.id,
        status="active",
        start_date=now - timedelta(days=10),
        end_date=now - timedelta(days=1)
    )
    db_session.add(sub)
    db_session.commit()
    assert sub.is_active() is False


def test_days_remaining(db_session, stripe_plan):
    now = datetime.utcnow()
    sub = Subscription(
        user_id=1,
        stripe_plan_id=stripe_plan.id,
        status="active",
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=5)
    )
    db_session.add(sub)
    db_session.commit()
    remaining = sub.days_remaining()
    assert remaining == 5 or remaining == 4  # depending on timedelta rounding


def test_days_remaining_none(db_session, stripe_plan):
    now = datetime.utcnow()
    sub = Subscription(
        user_id=1,
        stripe_plan_id=stripe_plan.id,
        status="active",
        start_date=now - timedelta(days=1),
        end_date=None
    )
    db_session.add(sub)
    db_session.commit()
    assert sub.days_remaining() is None


def test_to_dict(db_session, stripe_plan):
    now = datetime.utcnow()
    sub = Subscription(
        user_id=1,
        stripe_plan_id=stripe_plan.id,
        status="active",
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=5)
    )
    db_session.add(sub)
    db_session.commit()
    d = sub.to_dict()
    assert d["user_id"] == 1
    assert d["stripe_plan_id"] == stripe_plan.id
    assert d["plan_name"] == "Basic"
    assert d["status"] == "active"
    assert d["is_active"] is True
    assert d["days_remaining"] >= 0

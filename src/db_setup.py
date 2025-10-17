from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash
from get_conn import get_connection_uri
from db_models import (
    Base,
    User,
    Recipe,
    Image,
    Subscription,
    StripePlan,
)

conn_string = get_connection_uri()

engine = create_engine(conn_string, echo=True)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("Finished creating tables")


# -------------------------------
# create dummy data
# -------------------------------

plan_basic = StripePlan(
    stripe_plan_id="plan_basic_001",
    name="Basic Plan",
    price=980.0,
    interval="month"
)
plan_premium = StripePlan(
    stripe_plan_id="plan_premium_001",
    name="Premium Plan",
    price=1980.0,
    interval="month"
)

user1 = User(
    name="Alice",
    email="alice@example.com",
    password_hash=generate_password_hash("hashed_pw_123"),
    disabled=False,
    created_at=datetime.utcnow(),
)

user2 = User(
    name="Bob",
    email="bob@example.com",
    password_hash=generate_password_hash("hashed_pw_456"),
    disabled=False,
    created_at=datetime.utcnow(),
)

sub1 = Subscription(
    user=user1,
    stripe_plan=plan_basic,
    status="active",
    start_date=datetime(2025, 1, 1),
    end_date=None,
)

sub2 = Subscription(
    user=user2,
    stripe_plan=plan_premium,
    status="canceled",
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 6, 1),
)

recipe1 = Recipe(
    user=user1,
    title="Healthy Chicken Salad",
    markdown_content="### Ingredients\n- Chicken\n- Lettuce\n- Olive oil",
    created_at=datetime.utcnow(),
)


image1 = Image(
    recipe=recipe1,
    image_url="https://example.com/chicken_salad.jpg",
    is_regenerated=False,
    created_at=datetime.utcnow(),
)

# -------------------------------
# input data
# -------------------------------

session.add_all(
    [
        plan_basic,
        plan_premium,
        user1,
        user2,
        sub1,
        sub2,
        recipe1,
        image1,
    ]
)

session.commit()
print("Inserted dummy data successfully")

# session.close()
# engine.dispose()
# print("Connection closed")

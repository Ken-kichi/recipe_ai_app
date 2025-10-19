import os
import stripe
import dotenv

dotenv.load_dotenv()
stripe.api_key = os.getenv("STRIPE_API_KEY")

# list = stripe.Price.list(limit=3)
# print("Available Prices:")
# for price in list.data:
#     print(f"- ID: {price.id}, Amount: {price.unit_amount} {price.currency}")

session = stripe.checkout.Session.create(
    payment_method_types=["card"],
    mode="subscription",
    line_items=[{"price": "price_1SJZL8KN40oDP97jOz81Dxwl", "quantity": 1}],
    success_url="https://example.com/success",
    cancel_url="https://example.com/cancel",
)
print(f"Checkout Session created successfully:{session.url}")

# print(f"Checkout Session ID: {session.id}")
# print(f"Checkout URL: {session.url}")

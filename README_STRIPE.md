Stripe integration usage

Environment variables required:

- STRIPE_API_KEY: Your Stripe secret key (sk_live... or sk_test...)
- STRIPE_WEBHOOK_SECRET: (optional but recommended) webhook signing secret
- STRIPE_SUCCESS_URL: URL to redirect after successful checkout
- STRIPE_CANCEL_URL: URL to redirect after cancelled checkout

Install dependency:

pip install stripe

Endpoints added:

GET /api/payments/plans
- Returns plans stored in DB (use `StripePlan` table)

POST /api/payments/create-checkout-session
- Params: plan_id (int), user_email (string)
- Creates a Stripe Checkout session and returns {checkout_session_id, checkout_url}

POST /api/payments/webhook
- Stripe webhook endpoint. Configure your Stripe dashboard to send events here.
- Handles `checkout.session.completed` and creates a Subscription record in DB for the user.

Notes:
- The implementation assumes `StripePlan.stripe_plan_id` contains a Stripe Price ID.
- Webhook signature verification is enabled when STRIPE_WEBHOOK_SECRET is set.
- You must create Stripe plans/prices and seed `StripePlan` rows in the DB with `stripe_plan_id` equal to the Price ID.

# 🧾 API設計書：レシピ生成AIアプリ

## 概要

このAPIは、AIを活用して1日の栄養素を満たすレシピを自動生成・管理するバックエンドです。
JWT認証によるセキュアなアクセス制御を行い、Stripeを用いたサブスクリプション課金と連携しています。

---

## 📂 エンドポイント一覧

| カテゴリ         | メソッド   | パス                                       | 説明                     | 認証       |
| ------------ | ------ | ---------------------------------------- | ---------------------- | -------- |
| Auth         | POST   | `/auth/register`                         | 新規ユーザー登録               | 不要       |
| Auth         | POST   | `/auth/login`                            | ログイン（JWT発行）            | 不要       |
| Auth         | GET    | `/auth/me`                               | 自分のユーザー情報取得            | 必要       |
| Recipes      | POST   | `/recipes/generate`                      | AIによるレシピ自動生成           | 必要（サブスク） |
| Recipes      | GET    | `/recipes`                               | レシピ一覧取得                | 必要       |
| Recipes      | GET    | `/recipes/{id}`                          | レシピ詳細取得                | 必要       |
| Recipes      | PUT    | `/recipes/{id}`                          | レシピ内容更新                | 必要       |
| Recipes      | DELETE | `/recipes/{id}`                          | レシピ削除                  | 必要       |
| Images       | POST   | `/recipes/{id}/images/regenerate`        | 画像再生成                  | 必要       |
| Images       | GET    | `/recipes/{id}/images`                   | レシピ画像一覧取得              | 必要       |
| Nutrition    | GET    | `/recipes/{id}/nutrition`                | 栄養素情報取得                | 必要       |
| Subscription | POST   | `/subscriptions/create-checkout-session` | Stripe Checkoutセッション作成 | 必要       |
| Subscription | POST   | `/subscriptions/webhook`                 | Stripe Webhook受信       | 不要       |
| Subscription | GET    | `/subscriptions/me`                      | 自分のサブスクリプション情報取得       | 必要       |

---

## 🔑 認証仕様（JWT）

| 項目    | 内容                                              |
| ----- | ----------------------------------------------- |
| 認証方式  | Bearer Token (JWT)                              |
| ヘッダー  | `Authorization: Bearer <token>`                 |
| 有効期限  | 24時間                                            |
| クレーム  | `sub` にユーザーID、`exp` に有効期限を格納                    |
| 発行    | `/auth/login` 成功時に返却                            |
| 保護API | `/recipes/*`, `/subscriptions/*`, `/auth/me` など |

---

## 👤 Auth API

### 🔹 `POST /auth/register`

**概要**: 新規ユーザーを登録します。

#### リクエスト

```json
{
  "email": "user@example.com",
  "password": "password123",
  "name": "Ken"
}
```

#### レスポンス

```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "Ken"
}
```

---

### 🔹 `POST /auth/login`

**概要**: ログインしてJWTトークンを発行します。

#### リクエスト

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

#### レスポンス

```json
{
  "access_token": "<JWT_TOKEN>",
  "token_type": "bearer"
}
```

---

### 🔹 `GET /auth/me`

**概要**: 認証済みユーザーの情報を取得します。

#### レスポンス

```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "Ken",
  "subscription_active": true
}
```

---

## 🍳 Recipe API

### 🔹 `POST /recipes/generate`

**概要**: AIを使ってレシピを自動生成します（サブスク必要）。

#### リクエスト

```json
{
  "meal_type": "breakfast",
  "calorie_target": 700
}
```

#### レスポンス

```json
{
  "id": 101,
  "title": "たまごと野菜の朝ごはんプレート",
  "description": "たんぱく質とビタミンをバランスよく摂取できる朝食。",
  "steps": [
    "野菜をカットする",
    "卵を焼く",
    "盛り付けて完成"
  ],
  "image_url": "https://example.com/recipe101.jpg",
  "nutrition_summary": {
    "protein": 20,
    "carbs": 45,
    "fat": 10,
    "calories": 700
  }
}
```

---

### 🔹 `GET /recipes`

**概要**: 自分のレシピ一覧を取得。

#### レスポンス

```json
[
  {
    "id": 101,
    "title": "たまごと野菜の朝ごはんプレート",
    "created_at": "2025-10-08T09:00:00"
  },
  {
    "id": 102,
    "title": "バランス昼食セット",
    "created_at": "2025-10-07T10:30:00"
  }
]
```

---

### 🔹 `GET /recipes/{id}`

**概要**: レシピ詳細を取得。

#### レスポンス

```json
{
  "id": 101,
  "title": "たまごと野菜の朝ごはんプレート",
  "markdown": "# 材料\n- 卵\n- 野菜\n\n# 手順\n1. ...",
  "images": ["https://example.com/img1.jpg"],
  "nutrition": {
    "protein": 20,
    "carbs": 45,
    "fat": 10
  }
}
```

---

### 🔹 `PUT /recipes/{id}`

**概要**: レシピ内容を編集。

#### リクエスト

```json
{
  "title": "朝ごはんプレート（改）",
  "markdown": "# 材料\n- 卵\n- 野菜\n- トマト\n\n# 手順\n1. ..."
}
```

#### レスポンス

```json
{
  "message": "Recipe updated successfully"
}
```

---

### 🔹 `DELETE /recipes/{id}`

**概要**: レシピを削除。

#### レスポンス

```json
{
  "message": "Recipe deleted"
}
```

---

## 🖼️ Image API

### 🔹 `POST /recipes/{id}/images/regenerate`

**概要**: レシピ画像を再生成。

#### レスポンス

```json
{
  "recipe_id": 101,
  "image_url": "https://example.com/new_image.jpg"
}
```

---

### 🔹 `GET /recipes/{id}/images`

**概要**: 画像一覧を取得。

#### レスポンス

```json
[
  "https://example.com/image1.jpg",
  "https://example.com/image2.jpg"
]
```

---

## 🧬 Nutrition API

### 🔹 `GET /recipes/{id}/nutrition`

**概要**: 栄養素情報を取得。

#### レスポンス

```json
{
  "protein": 20,
  "carbs": 45,
  "fat": 10,
  "calories": 700,
  "is_balanced": true
}
```

---

## 💳 Subscription API (Stripe)

### 🔹 `POST /subscriptions/create-checkout-session`

**概要**: StripeのCheckoutセッションを作成。

#### リクエスト

```json
{
  "plan_id": "price_12345"
}
```

#### レスポンス

```json
{
  "checkout_url": "https://checkout.stripe.com/pay/cs_test_123"
}
```

---

### 🔹 `POST /subscriptions/webhook`

**概要**: StripeからのWebhookを受信。支払いステータス更新。

#### 例: Stripe送信データ

```json
{
  "type": "checkout.session.completed",
  "data": {
    "object": {
      "customer_email": "user@example.com",
      "subscription": "sub_123"
    }
  }
}
```

#### レスポンス

```json
{ "message": "Webhook received" }
```

---

### 🔹 `GET /subscriptions/me`

**概要**: 自分のサブスクリプション情報を取得。

#### レスポンス

```json
{
  "status": "active",
  "plan": "premium_monthly",
  "renewal_date": "2025-11-08"
}
```

---

## 🧩 モデル構造（SQLAlchemy）

| モデル名                 | 主なカラム                                        | リレーション                                |
| -------------------- | -------------------------------------------- | ------------------------------------- |
| **User**             | id, email, password_hash, name               | 1:N Recipe, 1:1 Subscription          |
| **Recipe**           | id, user_id, title, markdown, created_at     | N:1 User, 1:N Step, 1:N Image         |
| **Step**             | id, recipe_id, description, order            | N:1 Recipe                            |
| **Image**            | id, recipe_id, url, created_at               | N:1 Recipe                            |
| **Ingredient**       | id, name, unit                               | N:N Recipe (through RecipeIngredient) |
| **RecipeIngredient** | recipe_id, ingredient_id, amount             | link table                            |
| **Nutrition**        | id, recipe_id, calories, protein, fat, carbs | 1:1 Recipe                            |
| **Subscription**     | id, user_id, stripe_customer_id, status      | N:1 User, 1:1 StripePlan              |
| **StripePlan**       | id, stripe_price_id, name, amount            | 1:N Subscription                      |

---

## ⚙️ ステータスコード仕様

| コード | 意味                    | 備考          |
| --- | --------------------- | ----------- |
| 200 | OK                    | 正常処理        |
| 201 | Created               | 登録成功（POST系） |
| 400 | Bad Request           | パラメータ不備     |
| 401 | Unauthorized          | JWT無効       |
| 403 | Forbidden             | 権限不足        |
| 404 | Not Found             | 対象リソースなし    |
| 500 | Internal Server Error | サーバーエラー     |



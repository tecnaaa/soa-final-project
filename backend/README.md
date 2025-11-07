# Backend (FastAPI microservices)

This folder contains a minimal scaffold for a backend organized as microservices using FastAPI.

Structure:

- services/
  - auth/        (Auth service - token/login example)
  - users/       (User CRUD example)
  - workout/     (Workout plans, exercises, progress)
  - nutrition/   (Nutrition-related endpoints example)
  - calories/    (Foods, recipes, calories DB)
  - coaching/    (Coaching sessions endpoints)
  - payment/     (Payment processing example)
- docker-compose.yml
- .env.example

Each service is a small FastAPI app with a `main.py`, `requirements.txt` and a `Dockerfile` so you can run them individually or with Docker Compose.

How to run (dev)

1) Run a single service directly with uvicorn (requires Python 3.10+):

```powershell
cd backend/services/auth
python -m pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

2) Run all services with Docker Compose (requires Docker):

```powershell
cd backend
docker-compose up --build
```

Notes
- The scaffold is intentionally minimal (in-memory / dummy data) — replace with DB, messaging, or auth as needed.
- Ports used: auth=8001, users=8002, nutrition=8003, payment=8004,
  workout=8005, calories=8006, coaching=8007

Service -> Database tables mapping (tóm tắt)
- auth: (authentication / token) — liên quan tới `users` để xác thực; không lưu users ở đây.
- users: `users`, `roles`, `user_subscriptions` (thông tin người dùng, profile, vai trò, đăng ký)
- workout: `workout_plans`, `exercises`, `progress` (kế hoạch tập, bài tập, tiến độ)
- nutrition: `meal_plans`, `daily_meals`, `ingredients` (kế hoạch dinh dưỡng, bữa ăn, thành phần)
- calories: `foods`, `recipes`, `recipe_ingredients` (cơ sở dữ liệu dinh dưỡng / công thức)
- coaching: `coaching_sessions` (buổi huấn luyện: pt, user, thời gian)
- payment: `subscriptions`, `user_subscriptions`, `transactions` (gói, đăng ký người dùng, giao dịch)

Lưu ý vận hành
- Hiện tại mỗi service dùng store in-memory cho mục đích demo — dữ liệu sẽ mất khi restart.
- Để production: thêm DB (Postgres/SQLite), migration, config connection strings trong `.env`.

Next steps (suggested):
- Add database per service (Postgres, MySQL) and migrations.
- Add shared libraries or use a private pip package for cross-service models.
- Add CI/CD and health checks.

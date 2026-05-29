# Content Moderation API

An AI-powered content moderation REST API built with FastAPI and OpenAI GPT-4o-mini. Analyzes and classifies text as safe, flagged, or rejected using background task processing via Celery and Redis.

---

## Live API

https://www.raynercodes.dev

## Interactive Docs

https://www.raynercodes.dev/docs

> Test every endpoint directly in the browser — no Postman needed. Use `demo` / `demo123` to get started instantly.

---

## Features

- AI content moderation via OpenAI GPT-4o-mini
- Async background processing with Celery — responses return instantly without blocking
- JWT authentication with access and refresh token rotation
- Redis caching for completed moderation results and stats endpoints
- PostgreSQL with SQLAlchemy ORM and Alembic database migrations
- Rate limiting on the moderation endpoint to prevent API abuse
- Pagination on list endpoints
- Flower monitoring dashboard for Celery workers
- Structured logging for request tracing
- Dockerized with five services — API, worker, Flower, PostgreSQL, Redis

---

## Tech Stack

- Python
- FastAPI
- PostgreSQL + SQLAlchemy + Alembic
- Redis
- Celery
- OpenAI API (GPT-4o-mini)
- Docker / Docker Compose
- Nginx + Let's Encrypt SSL
- PyJWT
- Werkzeug

---

## Project Structure

```
routes/
services/
repos/
utils/
tasks/
migrations/
tests/
app.py
celery_app.py
database.py
models.py
config.py
Dockerfile
docker-compose.yml
```

---

## How to Run

### With Docker (recommended)

```bash
git clone https://github.com/raynercodes/content-moderation-api.git
cd content-moderation-api
cp .env.example .env  # add your secrets
docker compose up --build
```

### Manual Setup

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app:app --reload --port 8000
celery -A celery_app worker --loglevel=info
```

---

## Environment Variables

```
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/content_moderation
SECRET_KEY=your-secret-key
REDIS_URL=redis://redis:6379
OPENAI_API_KEY=your-openai-api-key
PORT=8000
```

---

## Authentication

```
POST /auth/register
POST /auth/login
POST /auth/refresh
```

Use the access token in all protected route headers:
```
Authorization: Bearer <access_token>
```

---

## Moderation Endpoints

```
POST   /moderations/          Submit content for moderation
GET    /moderations/          List moderation history (paginated)
GET    /moderations/stats     Get decision counts by type
GET    /moderations/{id}      Get a specific moderation result
```

### Pagination

```
GET /moderations/?page=1&limit=10
```

### Example Request

```json
{
  "content": "This is the text you want to moderate"
}
```

### Example Response

```json
{
  "success": true,
  "message": "Content moderated successfully",
  "data": {
    "id": 1,
    "content": "This is the text you want to moderate",
    "decision": "safe",
    "reason": "The content is appropriate and harmless.",
    "status": "completed",
    "created_at": "2026-05-29T10:00:00"
  },
  "meta": {}
}
```

### Decision Types

| Decision | Meaning |
|----------|---------|
| `safe` | Content is appropriate and harmless |
| `flagged` | Content is potentially problematic |
| `rejected` | Content is clearly harmful or abusive |

---

## Async Processing Flow

```
Client submits content
        ↓
API creates moderation record (status: pending)
        ↓
Task ID pushed to Redis queue
        ↓
API returns immediately with pending status
        ↓
Celery worker picks up task via BLPOP
        ↓
Worker calls OpenAI API
        ↓
Result saved to PostgreSQL (status: completed)
        ↓
Client polls GET /moderations/{id} for result
```

---

## Running Tests

```bash
pytest tests/ -v
```

Tests use a separate `content_moderation_test` database and mock all OpenAI API calls so no credits are consumed.

---

## Monitoring

Flower dashboard available at port `5555` for real-time Celery task monitoring.

---

## Design Decisions

### Celery for Background Processing
Moderation tasks are offloaded to Celery workers so the API returns instantly. Without this the client would wait 1-3 seconds for every OpenAI call.

### Redis as Message Broker and Cache
Redis serves two roles — task queue broker for Celery and cache for completed moderation results. Completed moderations are cached for 5 minutes since they never change. Stats are cached for 30 seconds.

### SQLAlchemy + Alembic
SQLAlchemy ORM provides clean database interactions and Alembic handles version-controlled schema migrations, making it safe to evolve the database schema without losing data.

### Conditional Caching
Results are only cached after status reaches `completed`. Pending results are never cached so clients always see the latest status.

### Rate Limiting
The moderation endpoint is rate limited to 10 requests per minute per IP to prevent abuse and control OpenAI API costs.

---

## Future Improvements

- WebSocket support for real-time moderation status updates
- Bulk moderation endpoint
- User-configurable moderation thresholds
- API versioning

---

## Author

Leonardo Rayner
github.com/raynercodes
www.raynercodes.dev
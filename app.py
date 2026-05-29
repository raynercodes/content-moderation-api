from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from fastapi.openapi.utils import get_openapi
from routes.auth_routes import router as auth_router
from routes.moderation_routes import router as moderation_router
from utils.logger import logger
from config import Config
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from utils.limiter import limiter

security = HTTPBearer()

app = FastAPI(
    title="Content Moderation API",
    description="""
    An AI powered content moderation API built with FastAPI and OpenAI via GPT-4o-mini.

    ## How to test in 3 steps
    **Step 1** — Register: use `POST /auth/register` or skip to Step 2 with the demo account

    **Step 2** — Login: use `POST /auth/login` with `username: demo` and `password: demo123`

    **Step 3** — Copy the `access_token` from the response

    **Step 4** — Click the **Authorize 🔒** button at the top right, paste your token, click Authorize

    You can now test all protected endpoints directly from this page.""",
    version="1.0.0"""
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth_router)
app.include_router(moderation_router)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request started method={request.method} path={request.url.path}")
    response = await call_next(request)
    logger.info(f"Request completed status={response.status_code}")
    return response

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"success": False, "message": str(exc), "data": None, "meta": {}}
    )

@app.exception_handler(Exception)
async def general_error_handler(request: Request, exc: Exception):
    logger.exception(f"Unexpected error path={request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error", "data": None, "meta": {}}
    )

@app.get("/")
def home(request: Request):
    base_url = str(request.base_url).rstrip("/")
    return {
        "name": "Content Moderation API",
        "description": "AI powered content moderation using OpenAI",
        "features": [
            "JWT authentication",
            "AI content moderation via OpenAI",
            "Moderation history with pagination",
            "Moderation stats",
            "Rate limiting",
            "PostgreSQL with Alembic migrations"
        ],
        "github": "https://github.com/raynercodes/content-moderation-api",
        "interactive_docs": f"{base_url}/docs",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=Config.PORT, reload=False)
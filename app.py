from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from routes.auth_routes import router as auth_router
from routes.moderation_routes import router as moderation_router
from utils.logger import logger
from config import Config

app = FastAPI(
    title="Content Moderation API",
    description="An AI powered content moderation API built with FastAPI and OpenAI",
    version="1.0.0"
)

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
def home():
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
        "docs": "/docs",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=Config.PORT, reload=False)
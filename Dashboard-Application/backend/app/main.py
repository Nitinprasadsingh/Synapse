from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.db.init_db import init_db
from app.api.v1 import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-grade API for AI-Driven Micro-Grid Load Balancing and Solar Energy Forecasting",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Startup event
@app.on_event("startup")
def startup_event():
    init_db()

# CORS Middleware
origins = [str(origin) for origin in settings.CORS_ORIGINS]
if "*" not in origins and "http://localhost:3000" not in origins:
    origins.append("http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if "*" not in origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

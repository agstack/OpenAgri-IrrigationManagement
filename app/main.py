from contextlib import asynccontextmanager

from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from api.api_v1.api import api_router

from core.config import settings
from init.init_gatekeeper import register_apis_to_gatekeeper

from jobs.background_tasks import get_weather_data

@asynccontextmanager
async def lifespan(fa: FastAPI):
    scheduler.add_job(get_weather_data, 'cron', day_of_week='*', hour=22, minute=0, second=0)
    scheduler.start()
    if settings.USING_GATEKEEPER:
        register_apis_to_gatekeeper()
    yield
    scheduler.shutdown()

app = FastAPI(
    title="Irrigation Management", openapi_url="/api/v1/openapi.json", lifespan=lifespan
)


jobstores = {
    'default': MemoryJobStore()
}

scheduler = AsyncIOScheduler(jobstores=jobstores)


if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix="/api/v1")

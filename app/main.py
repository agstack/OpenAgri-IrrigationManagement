import logging
import time
from contextlib import asynccontextmanager

from api.api_v1.api import api_router
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.config import settings
from fastapi import FastAPI
from init.init_gatekeeper import register_apis_to_gatekeeper
from init.init_soil_values import insert_soil_values_into_db
from init.init_kc import insert_crop_kc_into_db

from jobs.background_tasks import get_weather_data
from logging_config import configure_logging
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request


@asynccontextmanager
async def lifespan(fa: FastAPI):
    configure_logging()
    insert_soil_values_into_db()
    insert_crop_kc_into_db()
    scheduler.add_job(get_weather_data, 'cron', day_of_week='*', hour=22, minute=0, second=0)
    scheduler.start()
    if settings.USING_GATEKEEPER:
        register_apis_to_gatekeeper()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Irrigation Management", openapi_url="/api/v1/openapi.json", lifespan=lifespan
)


jobstores = {"default": MemoryJobStore()}

scheduler = AsyncIOScheduler(jobstores=jobstores)


if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

logger = logging.getLogger(__name__)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """log request response"""
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {duration:.4f}s"
    )
    return response


app.include_router(api_router, prefix="/api/v1")

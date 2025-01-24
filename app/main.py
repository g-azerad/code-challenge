import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from .dependencies import initialize_services, get_playwright_utils

@asynccontextmanager
async def lifespan(application: FastAPI):
    # Startup event
    print("Startup event triggered")
    initialize_services()
    playwright_utils = await get_playwright_utils()
    await playwright_utils.start()

    yield
    # Shutdown event
    print("Shutdown event triggered")
    await playwright_utils.stop()

# Creation of FastAPI application
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.cases import router as cases_router
from app.api.routes.diagnosis import router as diagnosis_router
from app.api.routes.health import router as health_router
from app.api.routes.history import router as history_router
from app.api.routes.patterns import router as patterns_router
from app.api.routes.samples import router as samples_router


DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5176",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
    "http://127.0.0.1:5176",
]


def _split_origins(value: str) -> list[str]:
    return [origin.strip() for origin in value.split(",") if origin.strip()]


def get_cors_origins() -> list[str]:
    configured = os.getenv("CORS_ORIGINS", "")
    frontend_origins = os.getenv("FRONTEND_ORIGINS", "")
    origins = _split_origins(configured) if configured.strip() else list(DEFAULT_CORS_ORIGINS)
    origins.extend(_split_origins(frontend_origins))
    return list(dict.fromkeys(origins))


app = FastAPI(
    title="Xiaohongshu Content Diagnosis Agent API",
    version="0.1.0",
    description="A compliant mock API for creator-owned Xiaohongshu note diagnosis.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_origin_regex=os.getenv("CORS_ORIGIN_REGEX") or None,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(diagnosis_router, prefix="/api/diagnose", tags=["diagnosis"])
app.include_router(cases_router, prefix="/api/cases", tags=["cases"])
app.include_router(samples_router, prefix="/api/samples", tags=["samples"])
app.include_router(patterns_router, prefix="/api/patterns", tags=["patterns"])
app.include_router(history_router, prefix="/api/history", tags=["history"])

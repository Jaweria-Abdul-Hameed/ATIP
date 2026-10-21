"""FastAPI modular monolith application entry point and lifespan configuration."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from atip_api.config import get_settings
from atip_api.core.errors import (
    APIException,
    api_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from atip_api.core.middleware import (
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
    TenantContextMiddleware,
    TimingMiddleware,
)
from atip_api.modules.agents.router import router as agents_router
from atip_api.modules.audit.router import router as audit_router
from atip_api.modules.github.router import router as github_router
from atip_api.modules.health.router import router as health_router
from atip_api.modules.identity.router import router as identity_router
from atip_api.modules.mining.router import router as mining_router
from atip_api.modules.organizations.router import router as organizations_router
from atip_api.modules.plans.router import router as plans_router
from atip_api.modules.reports.router import router as reports_router
from atip_api.modules.repositories.router import router as repositories_router
from atip_api.modules.risk.router import router as risk_router
from atip_api.modules.runs.router import router as runs_router
from atip_api.modules.whitebox.router import router as whitebox_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for resource initialization and teardown."""
    # Startup actions
    yield
    # Shutdown actions


def create_application() -> FastAPI:
    """Application factory configuring routes, middleware, and exception handlers."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="ATIP — Autonomous Testing Intelligence Platform Backend Modular Monolith API",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        lifespan=lifespan,
    )

    # Middlewares (order: outermost first)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(TenantContextMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception Handlers
    app.add_exception_handler(APIException, api_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Health probes at root
    app.include_router(health_router)

    # Modular API v1 routers
    v1_prefix = settings.API_V1_PREFIX
    app.include_router(identity_router, prefix=v1_prefix)
    app.include_router(organizations_router, prefix=v1_prefix)
    app.include_router(repositories_router, prefix=v1_prefix)
    app.include_router(github_router, prefix=v1_prefix)
    app.include_router(mining_router, prefix=v1_prefix)
    app.include_router(risk_router, prefix=v1_prefix)
    app.include_router(whitebox_router, prefix=v1_prefix)
    app.include_router(plans_router, prefix=v1_prefix)
    app.include_router(runs_router, prefix=v1_prefix)
    app.include_router(agents_router, prefix=v1_prefix)
    app.include_router(reports_router, prefix=v1_prefix)
    app.include_router(audit_router, prefix=v1_prefix)

    return app


app = create_application()


def run() -> None:
    """CLI entrypoint to run the uvicorn development server."""
    import uvicorn

    uvicorn.run("atip_api.main:app", host="0.0.0.0", port=8000, reload=True)

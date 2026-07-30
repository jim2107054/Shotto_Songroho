"""
Shotto Songroho — FastAPI Application Entry Point
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes import router
from app.services.vector_store import initialize_vector_store

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — initialize resources on startup."""
    logger.info("=" * 60)
    logger.info("Shotto Songroho — Starting up...")
    logger.info("=" * 60)

    # Initialize vector store and load corpus
    try:
        initialize_vector_store()
        logger.info("Vector store initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {e}", exc_info=True)
        logger.warning("Application will start but verification may not work correctly")

    logger.info("Shotto Songroho — Ready!")
    yield

    logger.info("Shotto Songroho — Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Shotto Songroho API",
    description="Agentic fact-verification for July Revolution claims. "
                "Submit text claims, images, or URLs and receive evidence-backed verdicts.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint — API info."""
    return {
        "name": "Shotto Songroho (শত্য সংগ্রহ)",
        "description": "Agentic Fact-Verification for July Revolution Claims",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "verify": "POST /api/verify",
            "corpus": "GET /api/corpus",
            "health": "GET /api/health",
            "chain_verify": "GET /api/chain/verify",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )

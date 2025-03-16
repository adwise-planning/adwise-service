import logging

import uvicorn
from fastapi import FastAPI

from app.config import Config
from app.extensions import init_extensions, SessionLocal, configure_logging
from app.routes import auth_routes, protected_routes

logger = logging.getLogger(__name__)  # Get logger for main module
config = Config()  # Instantiate Config once


# --- Lifespan ---
async def lifespan(application: FastAPI):
    logger.info("Application startup initiated...")
    try:
        application.config = config  # Attach config to app instance for easy access
        configure_logging(application)  # Configure logging

        with SessionLocal() as db:  # Use SessionLocal directly to create session
            # --- Initialize Extensions (Database, etc.) ---
            # Extensions are now initialized in lifespan startup event with database session
            init_extensions(application)  # Initialize extensions with db session, pass db to init_extensions
            logger.info("Database extensions initialized and tables created (if not exist).")
            # Example: Initialize Cache
            # initialize_cache(app)
            # logger.info("Cache initialized.")
            # Example: Register Health Checks
            # register_health_checks(app)
            # logger.info("Health checks registered.")
        logger.info("Application startup completed successfully.")
        yield  # Application is now running

    except Exception as e:
        logger.critical(f"Application startup failed: {e}", exc_info=True)
        # Optionally, perform cleanup or send alerts on startup failure
    finally:
        logger.info("Application shutdown initiated...")
        # --- Shutdown event handler ---
        # Example: Close database connections gracefully (handled by SessionLocal context manager)
        logger.info("Database connections closed (if applicable).")
        # Example: Shutdown background tasks/services
        # shutdown_background_tasks(app)
        # logger.info("Background tasks shutdown (if applicable).")
        logger.info("Application shutdown completed.")


def create_app():
    """
    Creates and configures the FastAPI application instance.
    Configures logging, initializes extensions, includes routes, and adds middleware and exception handlers.
    """
    application = FastAPI(lifespan=lifespan, description="Enterprise-Ready FastAPI Application", version="1.0.0")

    # --- Middleware ---
    # app.add_middleware(middleware.request_id_middleware)  # Add request ID middleware first
    # app.add_middleware(middleware.exception_logging_middleware)  # Add exception logging middleware

    # --- Include Routers (API Endpoints) ---
    application.include_router(auth_routes.router)
    application.include_router(protected_routes.router)

    # --- Exception Handlers ---
    logger.info("FastAPI application created and configured.")
    return application


app = create_app()  # Create FastAPI application instance

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=5000, reload=True,
                log_config=logging.basicConfig(level=config.LOG_LEVEL,
                                               format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s - %(message)s'))

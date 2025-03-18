import logging

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.config import Config
from app.extensions import init_extensions, SessionLocal, configure_logging
from app.routes import auth_routes, protected_routes

# Setting up logging
logger = logging.getLogger(__name__)
# Load configuration
config = Config()


# --- Lifespan ---
async def lifespan(application: FastAPI):
    logger.info("Application startup initiated...")
    try:
        application.config = config  # Attach config to app instance for easy access
        configure_logging(application)  # Configure logging settings

        # Initialize extensions like database or cache in a single block during startup
        with SessionLocal() as db:  # Using SessionLocal directly for session management
            init_extensions(application)  # Initialize extensions like DB connections
            logger.info("Database extensions initialized successfully.")

        logger.info("Application startup completed successfully.")
        yield  # Keep the app running

    except Exception as e:
        logger.critical(f"Application startup failed: {e}", exc_info=True)
        # Optionally, perform cleanup or send alerts on startup failure

    finally:
        logger.info("Application shutdown initiated...")
        # Graceful shutdown logic
        logger.info("Shutting down gracefully... Database connections and background tasks.")
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins, including localhost
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

if __name__ == "__main__":
    # Production-ready server setup using uvicorn
    uvicorn.run("app.main:app", host=config.HOST, port=config.PORT, reload=False, workers=1, access_log=True,
                log_config=logging.basicConfig(level=config.LOG_LEVEL,
                                               format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s - %(message)s'))

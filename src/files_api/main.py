import os

import pydantic
from fastapi import FastAPI


from files_api.settings import Settings
from files_api.routes import ROUTER
from src.errors import handle_broad_exception, handle_pydantic_validation_errors


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and return the FastAPI application instance."""
    # Use the provided settings or create a new Settings instance if none are given
    settings = settings or Settings(s3_bucket_name=os.environ["S3_BUCKET_NAME"])
    app = FastAPI()
    # Store the settings in the app's state for access throughout the app
    app.state.settings = settings
    # Register the API router with the FastAPI app
    app.include_router(ROUTER)
    # Add a custom exception handler for Pydantic validation errors
    app.add_exception_handler(
        exc_class_or_status_code=pydantic.ValidationError,
        handler=handle_pydantic_validation_errors,
    )
    # Add a middleware to handle broad exceptions and return appropriate responses
    app.middleware("http")(handle_broad_exception)
    # Return the configured FastAPI application instance
    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(ROUTER, host="0.0.0.0", port=8000)

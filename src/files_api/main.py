import os
from datetime import datetime
from typing import (
    List,
    Optional,
)

from fastapi import (
    Depends,
    FastAPI,
    APIRouter,
    HTTPException,
    Response,
    UploadFile,
    status,
    Request,
)
from fastapi.responses import StreamingResponse
from botocore.exceptions import ClientError

from files_api.settings import Settings
from files_api.s3.delete_objects import delete_s3_object
from files_api.s3.read_objects import (
    fetch_s3_object,
    fetch_s3_objects_metadata,
    fetch_s3_objects_using_page_token,
    object_exists_in_s3,
)
from files_api.s3.write_objects import upload_s3_object
from files_api.routes import ROUTER



def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and return the FastAPI application instance."""
    settings = settings or Settings()
    app = FastAPI()
    app.state.settings = settings
    app.include_router(ROUTER)
    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(ROUTER, host="0.0.0.0", port=8000)

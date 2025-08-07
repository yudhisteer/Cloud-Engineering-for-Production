# src/files_api/schemas.py
from datetime import datetime
from typing import (
    List,
    Optional,
)

from pydantic import (
    BaseModel,
    Field,
)

####################################
# --- Request/response schemas --- #
####################################


# constants
DEFAULT_GET_FILES_PAGE_SIZE = 10
DEFAULT_GET_FILES_MIN_PAGE_SIZE = 10
DEFAULT_GET_FILES_MAX_PAGE_SIZE = 100
DEFAULT_GET_FILES_DIRECTORY = ""


# read (cRud)
class FileMetadata(BaseModel):
    file_path: str
    last_modified: datetime
    size_bytes: int

# read (cRud)
class GetFilesResponse(BaseModel):
    files: List[FileMetadata]
    next_page_token: Optional[str]


# read (cRud)
class GetFilesQueryParams(BaseModel):
    page_size: int = Field(
        DEFAULT_GET_FILES_PAGE_SIZE,
        ge=DEFAULT_GET_FILES_MIN_PAGE_SIZE,
        le=DEFAULT_GET_FILES_MAX_PAGE_SIZE,
    )
    directory: Optional[str] = Field(
        DEFAULT_GET_FILES_DIRECTORY,
    )
    page_token: Optional[str] = None


# delete (cruD)
class DeleteFileResponse(BaseModel):
    message: str


# create/update (CrUd)
class PutFileResponse(BaseModel):
    file_path: str
    message: str
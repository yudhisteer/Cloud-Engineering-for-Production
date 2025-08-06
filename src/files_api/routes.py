import os


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

from files_api.s3.delete_objects import delete_s3_object
from files_api.s3.read_objects import (
    fetch_s3_object,
    fetch_s3_objects_metadata,
    fetch_s3_objects_using_page_token,
    object_exists_in_s3,
)
from files_api.s3.write_objects import upload_s3_object
from files_api.schemas import *

##################
# --- Routes --- #
##################

ROUTER = APIRouter()



@ROUTER.put("/files/{file_path:path}")
async def upload_file(request: Request, file_path: str, file: UploadFile, response: Response) -> PutFileResponse:
    """Upload a file."""
    s3_bucket_name = request.app.state.s3_bucket_name
    # Check if the file already exists in S3
    object_already_exists = object_exists_in_s3(
        bucket_name=s3_bucket_name,
        object_key=file_path,
    )
    if object_already_exists:
        response_message = f"Existing file updated at path: /{file_path}"
        # response.status_code = status.HTTP_204_NO_CONTENT #  does not return a response body
        response.status_code = status.HTTP_200_OK
    else:
        response_message = f"New file uploaded at path: /{file_path}"
        response.status_code = status.HTTP_201_CREATED

    # Read the file contents and upload to S3
    file_contents = await file.read()
    upload_s3_object(
        bucket_name=s3_bucket_name,
        object_key=file_path,
        file_content=file_contents,
        content_type=file.content_type,
    )

    return PutFileResponse(
        file_path=file_path,
        message=response_message,
    )



@ROUTER.get("/files")
async def list_files(
    request: Request,
    query_params: GetFilesQueryParams = Depends(),  # noqa: B008
) -> GetFilesResponse:
    """List files with pagination."""
    s3_bucket_name = request.app.state.s3_bucket_name
    # Validate page size
    if query_params.page_token:
        # If a page token is provided, fetch the next page of files
        files, next_page_token = fetch_s3_objects_using_page_token(
            bucket_name=s3_bucket_name,
            continuation_token=query_params.page_token,
            max_keys=query_params.page_size,
        )
    else:
        # If no page token is provided, fetch the first page of files
        files, next_page_token = fetch_s3_objects_metadata(
            bucket_name=s3_bucket_name,
            prefix=query_params.directory,
            max_keys=query_params.page_size,
        )

    # Convert the list of files to FileMetadata objects
    file_metadata_objs = [
        FileMetadata(
            file_path=f"{item['Key']}",
            last_modified=item["LastModified"],
            size_bytes=item["Size"],
        )
        for item in files
    ]

    return GetFilesResponse(
        files=file_metadata_objs, 
        next_page_token=next_page_token if next_page_token else None
        )


@ROUTER.get("/files/{file_path:path}")
async def get_file(
    request: Request,
    file_path: str,
) -> StreamingResponse:
    """Retrieve a file."""
    try:
        s3_bucket_name = request.app.state.s3_bucket_name
        # Fetch the file from S3
        # Note: file_path is the full path in S3, including any directories
        get_object_response = fetch_s3_object(s3_bucket_name, object_key=file_path)
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            raise HTTPException(status_code=404, detail="File not found")
        raise

    # Return the file as a streaming response
    # This allows large files to be sent efficiently without loading them fully into memory
    # The StreamingResponse will automatically set the Content-Type header based on the file's MIME type
    return StreamingResponse(
        content=get_object_response["Body"],
        media_type=get_object_response["ContentType"],
    )


@ROUTER.head("/files/{file_path:path}")
async def get_file_metadata(request: Request, file_path: str, response: Response) -> Response:
    """Retrieve file metadata.

    Note: by convention, HEAD requests MUST NOT return a body in the response.
    """
    try:
        s3_bucket_name = request.app.state.s3_bucket_name
        # Fetch the file metadata from S3
        get_object_response = fetch_s3_object(s3_bucket_name, object_key=file_path)
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            raise HTTPException(status_code=404, detail="File not found")
        raise

    # Set the response headers based on the S3 object metadata
    response.headers["Content-Type"] = get_object_response["ContentType"]
    response.headers["Content-Length"] = str(get_object_response["ContentLength"])
    response.headers["Last-Modified"] = get_object_response["LastModified"].strftime("%a, %d %b %Y %H:%M:%S GMT")

    # Set the status code to 200 OK
    # HEAD requests do not return a body, so we just set the status code and headers
    response.status_code = status.HTTP_200_OK
    
    return response


@ROUTER.delete("/files/{file_path:path}")
async def delete_file(
    request: Request,
    file_path: str,
    response: Response,
) -> Response:
    """Delete a file.

    NOTE: DELETE requests MUST NOT return a body in the response."""
    # Delete the file from S3
    s3_bucket_name = request.app.state.s3_bucket_name
    delete_s3_object(
        bucket_name=s3_bucket_name,
        object_key=file_path,
    )
    # Set the response status code to 204 No Content
    # This indicates that the request was successful and there is no content to return
    response.status_code = status.HTTP_204_NO_CONTENT
    
    return response



import boto3
from fastapi import status
from fastapi.testclient import TestClient

from files_api.schemas import DEFAULT_GET_FILES_MAX_PAGE_SIZE
from src.utils import delete_s3_bucket
from tests.consts import TEST_BUCKET_NAME


def test__get__nonexistent__file(client: TestClient):
    # Tests: GET /files/{file_path:path} endpoint (file retrieval)
    response = client.get("/files/nonexistent.txt")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "File not found"}


def test__head__nonexistent__file(client: TestClient):
    # Tests: HEAD /files/{file_path:path} endpoint (file metadata)
    response = client.head("/files/nonexistent.txt")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    # HEAD requests should not return a body, so we don't check response.json()
    assert response.content == b""


def test__delete__nonexistent__file(client: TestClient):
    # Tests: DELETE /files/{file_path:path} endpoint (file deletion)
    response = client.delete("/files/nonexistent.txt")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "File not found"}


def test_get_files_invalid_page_size(client: TestClient):
    response = client.get("/files?page_size=-1")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    response = client.get(f"/files?page_size={DEFAULT_GET_FILES_MAX_PAGE_SIZE + 1}")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_files_page_token_is_mutually_exclusive_with_page_size_and_directory(client: TestClient):
    response = client.get("/files?page_token=token&page_size=10")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "mutually exclusive" in str(response.json())

    response = client.get("/files?page_token=token&directory=dir")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "mutually exclusive" in str(response.json())

    response = client.get("/files?page_token=token&page_size=10&directory=dir")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "mutually exclusive" in str(response.json())


def test_unforeseemn_500_error(client: TestClient):
    # delete s3 bucket and all objects in it
    delete_s3_bucket(TEST_BUCKET_NAME)

    # make a request to the API to a route that interacts with the s3
    response = client.get("/files")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Internal server error"}

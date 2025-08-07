from fastapi import status
from fastapi.testclient import TestClient

from files_api.schemas import DEFAULT_GET_FILES_MAX_PAGE_SIZE


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


def test__get__files__invalid__page__size(client: TestClient):
    # Tests: GET /files endpoint (file listing) with invalid query parameter
    response = client.get("/files?page_size=-1")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test: GET /files endpoint (file listing) with invalid page size
    response = client.get(f"/files?page_size={DEFAULT_GET_FILES_MAX_PAGE_SIZE + 1}")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


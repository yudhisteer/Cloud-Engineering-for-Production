import botocore
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from files_api.settings import Settings
from src.files_api.main import create_app
from tests.consts import TEST_BUCKET_NAME

# Constants for testing
TEST_FILE_PATH = "test.txt"
TEST_FILE_CONTENT = b"Hello, world!"
TEST_FILE_CONTENT_TYPE = "text/plain"


# Fixture for FastAPI test client
@pytest.fixture
def client(mocked_aws) -> TestClient:  # pylint: disable=unused-argument
    settings: Settings = Settings(s3_bucket_name=TEST_BUCKET_NAME)
    app = create_app(settings=settings)
    with TestClient(app) as client:
        yield client


def test__upload__file(client: TestClient):
    # upload the file
    response = client.put(
        f"/files/{TEST_FILE_PATH}",
        files={"file": (TEST_FILE_PATH, TEST_FILE_CONTENT, TEST_FILE_CONTENT_TYPE)},
    )

    # check that the file was uploaded
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["file_path"] == TEST_FILE_PATH
    assert response_data["message"] == f"New file uploaded at path: /{TEST_FILE_PATH}"

    # update existing file
    updated_content = b"some updated content"
    response = client.put(
        f"/files/{TEST_FILE_PATH}",
        files={"file": (TEST_FILE_PATH, updated_content, TEST_FILE_CONTENT_TYPE)},
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["file_path"] == TEST_FILE_PATH
    assert response_data["message"] == f"Existing file updated at path: /{TEST_FILE_PATH}"


def test__list__files__with__pagination(client: TestClient):
    # Upload files
    for i in range(15):
        client.put(
            f"/files/file{i}.txt",
            files={"file": (f"file{i}.txt", TEST_FILE_CONTENT, TEST_FILE_CONTENT_TYPE)},
        )
    # List files with page size 10
    response = client.get("/files?page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["files"]) == 10
    assert "next_page_token" in data


def test__get__file__metadata(client: TestClient):
    # Upload a file
    client.put(
        f"/files/{TEST_FILE_PATH}",
        files={"file": (TEST_FILE_PATH, TEST_FILE_CONTENT, TEST_FILE_CONTENT_TYPE)},
    )
    # Get file metadata
    response = client.head(f"/files/{TEST_FILE_PATH}")
    assert response.status_code == 200
    headers = response.headers
    assert headers["Content-Type"] == TEST_FILE_CONTENT_TYPE
    assert headers["Content-Length"] == str(len(TEST_FILE_CONTENT))
    assert "Last-Modified" in headers


def test__get__file(client: TestClient):
    # Upload a file
    client.put(
        f"/files/{TEST_FILE_PATH}",
        files={"file": (TEST_FILE_PATH, TEST_FILE_CONTENT, TEST_FILE_CONTENT_TYPE)},
    )
    # Get file
    response = client.get(f"/files/{TEST_FILE_PATH}")
    assert response.status_code == 200
    assert response.content == TEST_FILE_CONTENT


def test__delete__file(client: TestClient):
    # Upload a file
    client.put(
        f"/files/{TEST_FILE_PATH}",
        files={"file": (TEST_FILE_PATH, TEST_FILE_CONTENT, TEST_FILE_CONTENT_TYPE)},
    )

    # Delete file
    response = client.delete(f"/files/{TEST_FILE_PATH}")
    assert response.status_code == 204

    # Verify deletion
    # The API should return a 404 status code when trying to get a deleted file
    response = client.get(f"/files/{TEST_FILE_PATH}")
    assert response.status_code == 404
import botocore
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.files_api.main import APP
from src.files_api.main import create_app
from tests.consts import TEST_BUCKET_NAME

# Constants for testing
TEST_FILE_PATH = "test.txt"
TEST_FILE_CONTENT = b"Hello, world!"
TEST_FILE_CONTENT_TYPE = "text/plain"


# Fixture for FastAPI test client
@pytest.fixture
def client(mocked_aws) -> TestClient:  # pylint: disable=unused-argument
    app = create_app(s3_bucket_name=TEST_BUCKET_NAME)
    with TestClient(app) as client:
        yield client


def test__upload__file(client: TestClient):
    # create a file
    test_file_path = "some/nested/file.txt"
    test_file_content = b"some content"
    test_file_content_type = "text/plain"

    # upload the file
    response = client.put(
        f"/files/{test_file_path}",
        files={"file": (test_file_path, test_file_content, test_file_content_type)},
    )

    # check that the file was uploaded
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["file_path"] == test_file_path
    assert response_data["message"] == f"New file uploaded at path: /{test_file_path}"

    # update existing file
    updated_content = b"some updated content"
    response = client.put(
        f"/files/{test_file_path}",
        files={"file": (test_file_path, updated_content, test_file_content_type)},
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["file_path"] == test_file_path
    assert response_data["message"] == f"Existing file updated at path: /{test_file_path}"


def test_list_files_with_pagination(client: TestClient):
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


def test_get_file_metadata(client: TestClient):
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


def test_get_file(client: TestClient):
    # Upload a file
    client.put(
        f"/files/{TEST_FILE_PATH}",
        files={"file": (TEST_FILE_PATH, TEST_FILE_CONTENT, TEST_FILE_CONTENT_TYPE)},
    )
    # Get file
    response = client.get(f"/files/{TEST_FILE_PATH}")
    assert response.status_code == 200
    assert response.content == TEST_FILE_CONTENT


def test_delete_file(client: TestClient):
    # Upload a file
    client.put(
        f"/files/{TEST_FILE_PATH}",
        files={"file": (TEST_FILE_PATH, TEST_FILE_CONTENT, TEST_FILE_CONTENT_TYPE)},
    )

    # Delete file
    response = client.delete(f"/files/{TEST_FILE_PATH}")
    assert response.status_code == 204

    # Verify deletion
    #
    # NOTE: this is an anti-pattern. The tests should be unaware of the internal implementation details
    # of the REST API. In this case, because the file is deleted from the S3 bucket, boto3 raises a NoSuchKey
    # exception when trying to fetch the file. This block succeeds only if a botocore exception is thrown.
    #
    # Later we will fix this by doing better error handling within the API itself.
    with pytest.raises(botocore.exceptions.ClientError):
        response = client.get(f"/files/{TEST_FILE_PATH}")
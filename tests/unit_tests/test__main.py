import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.files_api.main import APP


# Fixture for FastAPI test client
@pytest.fixture
def client(mocked_aws) -> TestClient:  # pylint: disable=unused-argument
    with TestClient(APP) as client:
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
    assert "last_modified" in response_data

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
    assert "last_modified" in response_data


def test_list_files_with_pagination(client: TestClient): ...


def test_get_file_metadata(client: TestClient): ...


def test_get_file(client: TestClient): ...


def test_delete_file(client: TestClient): ...
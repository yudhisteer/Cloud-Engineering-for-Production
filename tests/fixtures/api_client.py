import pytest
from fastapi.testclient import TestClient
from typing import Generator
from files_api.settings import Settings
from files_api.main import create_app
from tests.consts import TEST_BUCKET_NAME



# Fixture for FastAPI test client
@pytest.fixture
def client(mocked_aws) -> Generator[TestClient, None, None]:  # pylint: disable=unused-argument
    settings: Settings = Settings(s3_bucket_name=TEST_BUCKET_NAME)
    app = create_app(settings=settings)
    with TestClient(app) as client:
        yield client

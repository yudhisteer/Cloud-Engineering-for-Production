import os
from typing import Generator

import boto3
from moto import mock_aws
from pytest import fixture

from tests.consts import TEST_BUCKET_NAME


def point_away_from_aws() -> None:
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_REGION"] = "us-east-1"

@fixture
def mocked_aws() -> Generator[None, None, None]:
    with mock_aws():
        point_away_from_aws()
        # create an s3 bucket
        s3_client = boto3.client("s3")
        s3_client.create_bucket(Bucket=TEST_BUCKET_NAME)

        yield

        # clean by deleting the bucket and all its objects
        list_response = s3_client.list_objects_v2(Bucket=TEST_BUCKET_NAME)
        for obj in list_response.get("Contents", []):
            if "Key" in obj:
                s3_client.delete_object(Bucket=TEST_BUCKET_NAME, Key=obj["Key"])
        s3_client.delete_bucket(Bucket=TEST_BUCKET_NAME)
import os
from typing import Generator

import boto3
import botocore
from moto import mock_aws
from pytest import fixture

from tests.consts import TEST_BUCKET_NAME
from src.utils import delete_s3_bucket


def point_away_from_aws() -> None:
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_REGION"] = "us-east-1"


@fixture
def mocked_aws() -> Generator[None, None, None]:
    with mock_aws():
        # point away from aws, so that we don't use the real aws credentials
        point_away_from_aws()

        # create an s3 bucket
        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket=TEST_BUCKET_NAME)

        yield

        # clean by deleting the bucket and all its objects
        # we do not need to delete if the bucket does not exist
        try:
            delete_s3_bucket(TEST_BUCKET_NAME)
        except botocore.exceptions.ClientError as err:
            if err.response["Error"]["Code"] == "NoSuchBucket":
                pass
            else:
                raise


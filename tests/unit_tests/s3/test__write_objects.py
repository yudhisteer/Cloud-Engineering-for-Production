import boto3

try:
    from mypy_boto3_s3.type_defs import (
        GetObjectOutputTypeDef,
        ListObjectsV2OutputTypeDef,
    )
except ImportError:
    print("mypy-boto3-s3 is not installed, skipping type checking")

from files_api.s3.write_objects import upload_s3_object
from tests.consts import TEST_BUCKET_NAME


def test__upload_s3_object(mocked_aws: None) -> None:
    # upload a file to the bucket, with a particular content type
    object_key = "test.txt"
    file_content: bytes = b"Hello, world!"
    content_type = "text/plain"
    bucket_name = TEST_BUCKET_NAME
    upload_s3_object(
        bucket_name=bucket_name,
        object_key=object_key,
        file_content=file_content,
        content_type=content_type,
    )

    # check that the file was uploaded with the correct content type
    s3_client = boto3.client("s3", region_name="us-east-1")
    response: GetObjectOutputTypeDef = s3_client.get_object(Bucket=TEST_BUCKET_NAME, Key=object_key)
    assert response["Body"].read() == file_content
    assert response["ContentType"] == content_type
    
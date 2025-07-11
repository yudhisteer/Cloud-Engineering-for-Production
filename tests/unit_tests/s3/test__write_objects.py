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


def test__upload_s3_object() -> None:
    # create a bucket
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket=TEST_BUCKET_NAME)

    # upload a file to the bucket, with a particular content type
    object_key = "test.txt"
    file_content: bytes = b"Hello, world!"
    content_type = "text/plain"
    upload_s3_object(
        bucket_name=TEST_BUCKET_NAME,
        object_key=object_key,
        file_content=file_content,
        content_type=content_type,
    )

    # check that the file was uploaded with the correct content type
    s3_client = boto3.client("s3")
    response: GetObjectOutputTypeDef = s3_client.get_object(Bucket=TEST_BUCKET_NAME, Key=object_key)
    assert response["Body"].read() == file_content
    assert response["ContentType"] == content_type
    
    # delete  all objects in the bucket and the bucket itself
    list_response: ListObjectsV2OutputTypeDef = s3_client.list_objects_v2(Bucket=TEST_BUCKET_NAME)
    for obj in list_response.get("Contents", []):
        if "Key" in obj:
            s3_client.delete_object(Bucket=TEST_BUCKET_NAME, Key=obj["Key"])
    s3_client.delete_bucket(Bucket=TEST_BUCKET_NAME)

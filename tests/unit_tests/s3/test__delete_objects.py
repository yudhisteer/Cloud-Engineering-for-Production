"""Test cases for `s3.delete_objects`."""

import boto3

from files_api.s3.delete_objects import delete_s3_object
from files_api.s3.read_objects import object_exists_in_s3
from files_api.s3.write_objects import upload_s3_object
from tests.consts import TEST_BUCKET_NAME


def test_delete_existing_s3_object(mocked_aws: None): 
    # create a mock s3 client
    s3_client = boto3.client('s3')
    # upload a file to the bucket
    s3_client.put_object(Bucket=TEST_BUCKET_NAME, Key="testfile.txt", Body="test content")
    # delete the file
    delete_s3_object(TEST_BUCKET_NAME, "testfile.txt")
    # check that the file is deleted
    assert not object_exists_in_s3(TEST_BUCKET_NAME, "testfile.txt")


def test_delete_nonexistent_s3_object(mocked_aws: None):
    # upload a file to the bucket
    upload_s3_object(TEST_BUCKET_NAME, "testfile.txt", b"test content")
    # delete the file
    delete_s3_object(TEST_BUCKET_NAME, "testfile.txt")
    # delete the file again
    delete_s3_object(TEST_BUCKET_NAME, "testfile.txt")
    # check that the file is deleted as it should be
    assert object_exists_in_s3(TEST_BUCKET_NAME, "testfile.txt") is False
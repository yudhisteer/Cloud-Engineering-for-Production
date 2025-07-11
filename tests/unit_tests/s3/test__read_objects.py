"""Test cases for `s3.read_objects`."""

import boto3

from files_api.s3.read_objects import (
    fetch_s3_objects_metadata,
    fetch_s3_objects_using_page_token,
    object_exists_in_s3,
)
from tests.consts import TEST_BUCKET_NAME


def test_object_exists_in_s3(mocked_aws: None): 
    s3_client = boto3.client("s3", region_name="us-east-1")
    s3_client.put_object(Bucket=TEST_BUCKET_NAME, Key="test.txt", Body=b"test content")
    assert object_exists_in_s3(TEST_BUCKET_NAME, "test.txt", s3_client) == True
    assert object_exists_in_s3(TEST_BUCKET_NAME, "nonexistent.txt", s3_client) == False



def test_pagination(mocked_aws: None): 
    # Upload 10 objects
    s3_client = boto3.client("s3", region_name="us-east-1")
    for i in range(1, 11):
        print(f"Uploading object {i}")
        # we pad the object key with 0s to maintain lexicographic ordering
        s3_client.put_object(Bucket=TEST_BUCKET_NAME, Key=f"test_{i:02d}.txt", Body=f"content {i}")
    
    # paginating 3 at a time starting from 1 to 3
    files, next_continuation_token = fetch_s3_objects_metadata(TEST_BUCKET_NAME, max_keys=3)
    assert len(files) == 3
    assert files[0].get("Key") == "test_01.txt"
    assert files[1].get("Key") == "test_02.txt"
    assert files[2].get("Key") == "test_03.txt"

    # paginating 3 at a time starting from 4 to 6
    assert next_continuation_token is not None  # Type guard
    files, next_continuation_token = fetch_s3_objects_using_page_token(TEST_BUCKET_NAME, max_keys=3, continuation_token=next_continuation_token)
    assert len(files) == 3
    assert files[0].get("Key") == "test_04.txt"
    assert files[1].get("Key") == "test_05.txt"
    assert files[2].get("Key") == "test_06.txt"

    # Paginating 3 at a time starting from 7 to 9
    assert next_continuation_token is not None  # Type guard
    files, next_continuation_token = fetch_s3_objects_using_page_token(TEST_BUCKET_NAME, max_keys=3, continuation_token=next_continuation_token)
    assert len(files) == 3
    assert files[0].get("Key") == "test_07.txt"
    assert files[1].get("Key") == "test_08.txt"
    assert files[2].get("Key") == "test_09.txt"

    # Final page
    assert next_continuation_token is not None  # Type guard
    files, next_continuation_token = fetch_s3_objects_using_page_token(TEST_BUCKET_NAME, max_keys=1, continuation_token=next_continuation_token)
    assert len(files) == 1
    assert files[0].get("Key") == "test_10.txt"



def test_mixed_page_sizes(mocked_aws: None):

    s3_client = boto3.client("s3", region_name="us-east-1")
    for i in range(1, 8):
        # we pad the object key with 0s to maintain lexicographic ordering
        s3_client.put_object(Bucket=TEST_BUCKET_NAME, Key=f"test_{i:02d}.txt", Body=f"content {i}")

    # paginating 3 at a time starting from 1 to 2
    files, next_continuation_token = fetch_s3_objects_metadata(TEST_BUCKET_NAME, max_keys=2)
    assert len(files) == 2
    assert files[0].get("Key") == "test_01.txt"
    assert files[1].get("Key") == "test_02.txt"

    # paginating 3 at a time starting from 3 to 5
    assert next_continuation_token is not None  # Type guard
    files, next_continuation_token = fetch_s3_objects_using_page_token(TEST_BUCKET_NAME, max_keys=3, continuation_token=next_continuation_token)
    assert len(files) == 3
    assert files[0].get("Key") == "test_03.txt"
    assert files[1].get("Key") == "test_04.txt"
    assert files[2].get("Key") == "test_05.txt"

    # paginating 1 at a time starting from 6
    assert next_continuation_token is not None  # Type guard
    files, next_continuation_token = fetch_s3_objects_using_page_token(TEST_BUCKET_NAME, max_keys=1, continuation_token=next_continuation_token)
    assert len(files) == 1
    assert files[0].get("Key") == "test_06.txt"

    # final page
    assert next_continuation_token is not None  # Type guard
    files, next_continuation_token = fetch_s3_objects_using_page_token(TEST_BUCKET_NAME, max_keys=1, continuation_token=next_continuation_token)
    assert len(files) == 1
    assert files[0].get("Key") == "test_07.txt"







def test_directory_queries(mocked_aws: None): 
    s3_client = boto3.client("s3")

    # nested folder structure
    s3_client.put_object(Bucket=TEST_BUCKET_NAME, Key="folder1/file1.txt", Body="content 1")
    s3_client.put_object(Bucket=TEST_BUCKET_NAME, Key="folder1/file2.txt", Body="content 2")
    s3_client.put_object(Bucket=TEST_BUCKET_NAME, Key="folder2/file3.txt", Body="content 3")
    s3_client.put_object(Bucket=TEST_BUCKET_NAME, Key="folder2/subfolder1/file4.txt", Body="content 4")
    s3_client.put_object(Bucket=TEST_BUCKET_NAME, Key="file5.txt", Body="content 5")

    # Query with prefix
    files, next_page_token = fetch_s3_objects_metadata(TEST_BUCKET_NAME, prefix="folder1/")
    assert len(files) == 2
    assert files[0].get("Key") == "folder1/file1.txt"
    assert files[1].get("Key") == "folder1/file2.txt"
    assert next_page_token is None

    # Query with prefix for nested folder
    files, next_page_token = fetch_s3_objects_metadata(TEST_BUCKET_NAME, prefix="folder2/subfolder1/")
    assert len(files) == 1
    assert files[0].get("Key") == "folder2/subfolder1/file4.txt"
    assert next_page_token is None

    # Query with no prefix
    files, next_page_token = fetch_s3_objects_metadata(TEST_BUCKET_NAME)
    assert len(files) == 5
    assert files[0].get("Key") == "file5.txt"
    assert files[1].get("Key") == "folder1/file1.txt"
    assert files[2].get("Key") == "folder1/file2.txt"
    assert files[3].get("Key") == "folder2/file3.txt"
    assert files[4].get("Key") == "folder2/subfolder1/file4.txt"
    assert next_page_token is None
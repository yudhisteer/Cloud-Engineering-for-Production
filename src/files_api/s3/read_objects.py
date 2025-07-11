"""Functions for reading objects from an S3 bucket--the "R" in CRUD."""

from typing import Optional

import boto3
from botocore.exceptions import ClientError

try:
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_s3.type_defs import (
        GetObjectOutputTypeDef,
        ObjectTypeDef,
        ListObjectsV2OutputTypeDef,
    )
except ImportError:
    print("mypy-boto3-s3 is not installed, skipping type checking")


DEFAULT_MAX_KEYS = 1_000

OBJECT_NOT_FOUND_ERROR_CODE = "404"



def object_exists_in_s3(bucket_name: str, object_key: str, s3_client: Optional["S3Client"] = None) -> bool:
    """
    Check if an object exists in the S3 bucket using head_object.

    :param bucket_name: Name of the S3 bucket.
    :param object_key: Key of the object to check.
    :param s3_client: Optional S3 client to use. If not provided, a new client will be created.

    :return: True if the object exists, False otherwise.
    """
    if s3_client is None:
        s3_client = boto3.client('s3')
    
    # check if the object exists
    try:
        s3_client.head_object(Bucket=bucket_name, Key=object_key)
        return True
    except ClientError as err:
        if err.response.get("Error", {}).get("Code") == OBJECT_NOT_FOUND_ERROR_CODE:
            return False
        raise


def fetch_s3_object(
    bucket_name: str,
    object_key: str,
    s3_client: Optional["S3Client"] = None,
) -> "GetObjectOutputTypeDef":
    """
    Fetch metadata of an object in the S3 bucket.

    :param bucket_name: Name of the S3 bucket.
    :param object_key: Key of the object to fetch.
    :param s3_client: Optional S3 client to use. If not provided, a new client will be created.

    :return: Metadata of the object.
    """

    if s3_client is None:
        s3_client = boto3.client('s3')

    response: GetObjectOutputTypeDef = s3_client.get_object(Bucket=bucket_name, Key=object_key)

    return response


def fetch_s3_objects_using_page_token(
    bucket_name: str,
    continuation_token: str,
    max_keys: int | None = None,
    s3_client: Optional["S3Client"] = None,
) -> tuple[list["ObjectTypeDef"], Optional[str]]:
    """
    Fetch list of object keys and their metadata using a continuation token.

    :param bucket_name: Name of the S3 bucket to list objects from.
    :param continuation_token: Token for fetching the next page of results where the last page left off.
    :param max_keys: Maximum number of keys to return within this page.
    :param s3_client: Optional S3 client to use. If not provided, a new client will be created.

    :return: Tuple of a list of objects and the next continuation token.
        1. Possibly empty list of objects in the current page.
        2. Next continuation token if there are more pages, otherwise None.
    """
    if s3_client is None:
        s3_client = boto3.client('s3')

    if max_keys is None:
        max_keys = DEFAULT_MAX_KEYS

    response: ListObjectsV2OutputTypeDef = s3_client.list_objects_v2(Bucket=bucket_name, ContinuationToken=continuation_token, MaxKeys=max_keys)
    files: list["ObjectTypeDef"] = response.get("Contents", [])
    next_continuation_token: str | None = response.get("NextContinuationToken")

    return files, next_continuation_token


def fetch_s3_objects_metadata(
    bucket_name: str,
    prefix: Optional[str] = None,
    max_keys: Optional[int] = DEFAULT_MAX_KEYS,
    s3_client: Optional["S3Client"] = None,
) -> tuple[list["ObjectTypeDef"], Optional[str]]:
    """
    Fetch list of object keys and their metadata.

    :param bucket_name: Name of the S3 bucket to list objects from.
    :param prefix: Prefix to filter objects by.
    :param max_keys: Maximum number of keys to return within this page.
    :param s3_client: Optional S3 client to use. If not provided, a new client will be created.

    :return: Tuple of a list of objects and the next continuation token.
        1. Possibly empty list of objects in the current page.
        2. Next continuation token if there are more pages, otherwise None.
    """
    if s3_client is None:
        s3_client = boto3.client('s3')

    if max_keys is None:
        max_keys = DEFAULT_MAX_KEYS

    if prefix is None:
        prefix = ""

    response: ListObjectsV2OutputTypeDef = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix, MaxKeys=max_keys)
    files: list["ObjectTypeDef"] = response.get("Contents", [])
    next_continuation_token: str | None = response.get("NextContinuationToken")

    return files, next_continuation_token
    

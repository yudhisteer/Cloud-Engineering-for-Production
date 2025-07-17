# cloud-course-project


## Plan of Action
0. AWS CLI Basics
1. Read, Write, Delete with Boto3
2. HTTP and REST


-----------------------------------

## 0. AWS CLI Basics


### Create a new profile

```bash
aws configure sso --profile <profile-name>
```

List s3 buckets

```bash
aws s3 ls --profile <profile-name>
```

--------------------------------------

## 1. Read, Write, Delete with Boto3
We will now be writing some functions which will later be used for CRUD operations using FastAPI. For now, we will
concentrate on how to read, write, and delete objects in s3 using the Boto3 SDK. Note that below you will find 
explanations only for uploading objects in s3, the files [src/files_api/s3/read_objects.py](src/files_api/s3/read_objects.py) and [src/files_api/s3/delete_objects.py](src/files_api/s3/delete_objects.py) cover the other two operations.

### 1.1 Upload object in s3
To upload an object in s3, we will use the `put_object` method. This method takes the following parameters:
- Bucket: The name of the S3 bucket where the object will be stored.
- Key: The path (including the filename) for the object within the bucket.
- Body: The actual content of the file, as bytes.
- ContentType: The MIME type of the file (e.g., "text/plain" for a text file).

Note that we are creating a new s3 client if not provided. This is because we want to be able to use the same s3 client for all the operations. For the MIME type, we are setting it to `application/octet-stream` if not provided as this is the default MIME type for generic binary files since boto3 does not allow `ContentType` to be `None`. You can learn more about MIME types [here](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/MIME_types/Common_types) or in the appendix below.

```python
# src/files_api/s3/write_objects.py

"""Functions for writing objects from an S3 bucket--the "C" and "U" in CRUD."""

def upload_s3_object(
    bucket_name: str,
    object_key: str,
    file_content: bytes,
    content_type: Optional[str] = None,
    s3_client: Optional["S3Client"] = None,
) -> None:
    # create a new s3 client if not provided
    if s3_client is None:
        s3_client = boto3.client('s3')
    # set the content type if not provided
    content_type = content_type or "application/octet-stream"
    # upload the object to s3 using the upload_object method
    s3_client.put_object(
        Bucket=bucket_name,
        Key=object_key,
        Body=file_content,
        ContentType=content_type
    )
```

Now that we have our function, let's test it.

### 1.2 Unit Test with Boto3
To write a unit test, it is wise to mirror the directory structure of the code we are testing. In our case, we are testing the `write_objects.py` file, so we will create a `test__write_objects.py` file in the `tests/unit_tests/s3` directory. In that way, we can quickly identify the test file when we are looking at the codebase.

We need to create a `TEST_BUCKET_NAME` in the `tests/consts.py` file as we want to use the same bucket name for all the 
tests. We are using `"text/plain"` as the content type for the file we are uploading which is just a `.txt` file.

For any test, the steps are quite similar:
1. Do some setup
2. Run the function we are testing
3. Assert the results are as expected
4. Clean up as a test should be stateless

In our case, we are creating a bucket, uploading a file to it, checking that the file was uploaded with the correct content type, and then deleting the bucket and all the objects in it.
 
```python
# tests/unit_tests/s3/test__write_objects.py

from files_api.s3.write_objects import upload_s3_object
from tests.consts import TEST_BUCKET_NAME

def test__upload_s3_object() -> None:
    # 1. create a bucket
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket=TEST_BUCKET_NAME)

    # 2. upload a file to the bucket using the upload_s3_object function
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

    # 3. check that the file was uploaded with the correct content type
    response: GetObjectOutputTypeDef = s3_client.get_object(Bucket=TEST_BUCKET_NAME, Key=object_key)
    assert response["Body"].read() == file_content
    assert response["ContentType"] == content_type
    
    # 4. delete all objects in the bucket and the bucket itself
    list_response: ListObjectsV2OutputTypeDef = s3_client.list_objects_v2(Bucket=TEST_BUCKET_NAME)
    for obj in list_response.get("Contents", []):
        if "Key" in obj:
            s3_client.delete_object(Bucket=TEST_BUCKET_NAME, Key=obj["Key"])
    s3_client.delete_bucket(Bucket=TEST_BUCKET_NAME)
```

While it is a working unit test, there are 2 issues with it:

1. Everytime we run this test, we are creating a bucket, do some process, and then delete the bucket and all the objects in it. This is not efficient and can be time consuming. If not careful, we might delete the wrong bucket.
2. For all the other tests, we will need to create a bucket and then delete it.  We do not want to repeat this 
   for every test. The `setup` and `teardown` should be done only once.



### 1.3 Mocking Boto3 with Moto


### 1.4 Better testing with PyTest Fixtures




-------------------------------------------













Without mocking:



## Appendix

### MIME types

MIME (Multi-purpose Internet Mail Extensions) types are standardized identifiers that help browsers understand what type of content they're receiving over HTTP. When a web server sends a file, it includes a MIME type in the response headers, enabling the browser to handle the content appropriately—whether that's displaying an image, rendering HTML, or prompting a download.

Common MIME types include:
- `text/html` for HTML documents
- `image/jpeg` for JPEG images  
- `application/json` for JSON data
- `text/plain` for plain text files
- `application/pdf` for PDF documents

In our case, when we download a file from S3 with a specified `ContentType`, the browser will know how to render it.
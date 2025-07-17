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

Note that we are creating a new s3 client if not provided. This is because we want to be able to use the same s3 client for all the operations. For the MIME type, we are setting it to `application/octet-stream` if not provided as this is the default MIME type for binary files. You can learn more about MIME types [here](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/MIME_types/Common_types) or in the appendix below.

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


### 1.3 Mocking Boto3 with Moto


### 1.4 Better testing with PyTest Fixtures




-------------------------------------------













Without mocking:

```python
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
```


## Appendix

### MIME types

MIME (Multi-purpose Internet Mail Extensions) types are standardized identifiers that help browsers understand what type of content they're receiving over HTTP. When a web server sends a file, it includes a MIME type in the response headers, enabling the browser to handle the content appropriately—whether that's displaying an image, rendering HTML, or prompting a download.

Common MIME types include:
- `text/html` for HTML documents
- `image/jpeg` for JPEG images  
- `application/json` for JSON data
- `text/plain` for plain text files
- `application/pdf` for PDF documents

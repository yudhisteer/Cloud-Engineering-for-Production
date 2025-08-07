# cloud-course-project


## Plan of Action
0. AWS CLI Basics
1. Read, Write, Delete with Boto3
2. HTTP and REST
3. Endpoints
4. Twelve-Factor App


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

In the next section, we will fix both issues.

### 1.3 Fix 1: Mocking Boto3 with Moto
Now we want to test not with the real AWS resources, but with a **mocked** one. [Moto](https://docs.getmoto.org/en/latest/docs/getting_started.html) is a library that allows us to do just that. We just need to add the `@mock_aws` decorator to the test function and we are good to go! (Or, we can use the `with mock_aws():` context manager.)

#### How the Mock AWS Works ?

The `@mock_aws` decorator creates a testing environment that `simulates` AWS services **locally**:

- When we apply this decorator, it activates `Python context managers` that intercept all Boto3 client and resource creation. This process, known as `monkey patching`, replaces the original AWS connection methods with Moto's `mock` implementations.

- Once activated, any Boto3 client/resource we create operates within Moto's `simulated AWS environment` rather than connecting to real AWS services. All API calls are captured and processed by Moto's **internal state management system** instead of reaching AWS servers.

- Instead of modifying actual AWS resources, all operations (create, read, update, delete) work against Moto's `in-memory representation` of AWS services. This provides fast, isolated testing without any external dependencies or costs.

#### Limitations to Consider:

- **IAM Authorization**: Moto doesn't robustly simulate IAM permissions and access controls. By default, it assumes `full administrative access` to all mocked services.
- **Testing IAM Policies**: If we need to verify that specific IAM roles have appropriately restrictive permissions, we'll need additional testing strategies since Moto won't enforce these constraints. Instead [LocalStack](https://www.localstack.cloud/) which provides more functionalities but at a price.

Using Moto enables reliable, fast unit testing while avoiding the **complexity** and **cost** of interacting with real AWS infrastructure.

Using the `@mock_aws` decorator:

```python
from moto import mock_aws

@mock_aws # this is a decorator that will mock the s3 client
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

or using the `with mock_aws():` context manager:

```python
from moto import mock_aws


def upload_s3_object(
    bucket_name: str,
    object_key: str,
    file_content: bytes,
    content_type: Optional[str] = None,
    s3_client: Optional["S3Client"] = None,
) -> None:
    with mock_aws():
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

Before runing the tests, we need to make sure that we are using `testing environment variables` in order to avoid accidentally using the real AWS credentials.

```bash
export AWS_ACCESS_KEY_ID='testing'
export AWS_SECRET_ACCESS_KEY='testing'
export AWS_SECURITY_TOKEN='testing'
export AWS_SESSION_TOKEN='testing'
export AWS_DEFAULT_REGION='us-east-1'
```

We also need to setup the mock **BEFORE** we create the s3 client. If we do it after, the s3 client will be created with the real AWS credentials.

```python
# GOOD
with mock_aws():
    # s3 client is created within the context manager - mock AWS
    if s3_client is None:
        s3_client = boto3.client('s3')

# BAD
# s3 client is created outside the context manager - real AWS
if s3_client is None:
    s3_client = boto3.client('s3')

with mock_aws():
    ...
```


Each time we use the moto mock AWS context manager (such as with a `with mock_aws():` block), it creates a brand new, isolated mock AWS environment. Any resources we create, like S3 buckets, will only exist within that block. As soon as we exit the `with mock_aws():` block, all state is lost and the environment is reset.

```python
# first context manager
with mock_aws():
    # create a new s3 client if not provided
    if s3_client is None:
        s3_client = boto3.client('s3')


# second different context manager
with mock_aws():
    # create a new s3 client if not provided
    if s3_client is None:
        s3_client = boto3.client('s3')
```

To maintain persistent state across multiple tests, such as keeping a pre-created S3 bucket available, we need to make sure that all related setup and test code execute within the **same** `with mock_aws():` context manager block.


### 1.4 Fix 2: Unit Test with PyTest Fixtures

The ideal structure for a test is as follows:

1. **Setup:** Prepare any required state, such as creating an S3 bucket.
2. **Action:** Perform the operation you want to test, for example, uploading files to the bucket.
3. **Assertion:** Check that the operation had the expected effect, such as verifying that files were uploaded successfully.
4. **Cleanup:** Always clean up any state you created, regardless of whether the test passed or failed, to ensure tests remain stateless.

In our unit test function `test__upload_s3_object`, we do not properly handle the cleanup step. If step 3, the assertion, fails, the test will exit early and cleanup code will **NOT** run. This can lead to leftover resources, which is problematic especially if using real AWS resources, as it can cause unnecessary costs and confusion.

To fix this, we can use PyTest fixtures. Pytest fixtures allow you to have a **shared setup** and **teardown** of the testing logic. We register the fixtures in the `conftest.py` file.

```python
# tests/conftest.py
pytest_plugins = [
    "tests.fixtures.mocked_aws",
]
```

In the code below, we are implementing `step 1` and `step 4` in the `mocked_aws` function which is decorated with `@pytest.fixture(scope="function")`. This means that the function will be run before each test function.

```python
# tests/fixtures/mocked_aws.py

def point_away_from_aws() -> None:
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_REGION"] = "us-east-1"


@pytest.fixture(scope="function")
def mocked_aws() -> Generator[None, None, None]:
    with mock_aws():
        # point away from aws, so that we don't use the real aws credentials
        point_away_from_aws()

        # 1. create an s3 bucket
        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket=TEST_BUCKET_NAME)

        yield

        # 4. clean by deleting the bucket and all its objects
        list_response = s3_client.list_objects_v2(Bucket=TEST_BUCKET_NAME)
        for obj in list_response.get("Contents", []):
            if "Key" in obj:
                s3_client.delete_object(Bucket=TEST_BUCKET_NAME, Key=obj["Key"])
        s3_client.delete_bucket(Bucket=TEST_BUCKET_NAME)
        print(f"s3_client: {s3_client}")
        print("Finished mocked_aws")

```

VERY IMPORTANT:
The `yield` statement in our pytest fixture temporarily pauses the fixture, allowing the test code to run while keeping the `mock_aws()` context manager **active**. This ensures that the Moto mock environment remains in effect throughout the test. After the test completes, the fixture resumes after the `yield` to perform any necessary cleanup, still within the Moto context.

To use the fixture, we need to add the `mocked_aws` parameter to the test function.

```python
# tests/unit_tests/s3/test__write_objects.py

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
    
```

Now that we have a shared setup and teardown, we can write the `R` and `D` in the `CRUD` operations and their respective unit tests using the same fixture by mocking AWS with `moto`.

-------------------------------------------

## 2. HTTP and REST



-------------------------------------------


## 3. Endpoints
Let's look at some specs for the API to **Upload** or **Overwrite** files in S3. We will use FastAPI to create the endpoints.

### 3.1 Upload or Overwrite Files

We use the `PUT` method for both creating and updating files because the file path uniquely identifies each resource. Since the client always knows the full path (URN) of the file, `PUT` is appropriate for both operations. This approach ensures that each file can be created or replaced at a known location without ambiguity.

- Endpoint: `/files/{file_path:path}`
    - Method: `PUT`

- Request
    - Path Parameter: `file_path` (string, required) - The path where the file will be stored in S3.
    - Query Parameter: None
    - Request Body: `file` (file, required) - The file to be uploaded.
    - Notable Request Headers: 
        - `Content-Type` (string, required) - The MIME type of the file being uploaded (e.g., `text/plain`, `image/jpeg`).

    - Example Request:
        ```http
        PUT /files/my_folder/my_file.txt
        Content-Type: text/plain

        (file content here)
        ```

- Response
    - Status Codes:
        - `200 OK` - If the file was successfully updated.
        - `201 Created` - If a new file was successfully created.
    - Notable Response Headers: None
    - Response Payload (for 201 Created):
        ```json
        {
            "file_path": "my_folder/my_file.txt",
            "message": "New file uploaded at path: /my_folder/my_file.txt"
        }
        ```
    - Example Response (for 201 Created):
        ```json
        {
            "file_path": "my_folder/my_file.txt",
            "message": "New file uploaded at path: /my_folder/my_file.txt"
        }
        ```
        ```json
        {
            "file_path": "my_folder/my_file.txt",
            "message": "Existing file updated at path: /my_folder/my_file.txt"
        }
        ```

Note: We use Uses FastAPI's `UploadFile` to handle binary file uploads. `file.content_type` preserves the original content type of the uploaded file. While we do handle the `Content-Type`  via `file.content_type`, we don't explicitly validate or document that this header is required or notable. For the returned response, we define a `PutFileResponse` pydantic model to encapsulate the file path and a message indicating whether the file was newly created or updated. 


```python
# create/update (CrUd)
class PutFileResponse(BaseModel):
    file_path: str
    message: str


@APP.put("/files/{file_path:path}")
async def upload_file(file_path: str, file: UploadFile, response: Response) -> PutFileResponse:
    """Upload a file."""
    # Check if the file already exists in S3
    object_already_exists = object_exists_in_s3(
        bucket_name=S3_BUCKET_NAME,
        object_key=file_path,
    )
    if object_already_exists:
        response_message = f"Existing file updated at path: /{file_path}"
        # response.status_code = status.HTTP_204_NO_CONTENT #  does not return a response body
        response.status_code = status.HTTP_200_OK
    else:
        response_message = f"New file uploaded at path: /{file_path}"
        response.status_code = status.HTTP_201_CREATED

    # Read the file contents and upload to S3
    file_contents = await file.read()
    upload_s3_object(
        bucket_name=S3_BUCKET_NAME,
        object_key=file_path,
        file_content=file_contents,
        content_type=file.content_type,
    )

    return PutFileResponse(
        file_path=file_path,
        message=response_message,
    )

```

### 3.2 List Files
To list files in a specific folder, we will use the `GET` method. This method retrieves a list of files in the specified folder in S3.

- Endpoint: `/files`
    - Method: `GET`

- Request
    - Path Parameter: None
    - Query Parameters:
        - `directory` (string, optional) - The folder path to list files from.
        - `page_size` (integer, optional) - The number of files to return per page (default: 10, max: 100).
        - `page_token` (string, optional) - A token for pagination to fetch the next set of files.
      - Request Body: None
    - Notable Request Headers: None
    - Example Request:
        ```http
        GET /files?directory=my_folder&page_size=10&page_token=abc123
        ```

- Response
    - Status Codes:
        - `200 OK` - If the request was successful.
    - Notable Response Headers: None
    - Response Payload:
      - `files` (array of objects) - A list of file metadata objects, each containing:
        - `file_path` (string) - The path of the file in S3.
        - `last_modified` (string, ISO 8601 format) - The last modified timestamp of the file.
        - `size_bytes` (integer) - The size of the file in bytes.
      - `next_page_token` (string, optional) - A token to fetch the next page of results, if available.
    - Example Response:
        ```json
        {
            "files": [
                {
                    "file_path": "my_folder/file1.txt",
                    "last_modified": "2023-10-01T12:00:00Z",
                    "size_bytes": 1234
                },
                {
                    "file_path": "my_folder/file2.jpg",
                    "last_modified": "2023-10-02T15:30:00Z",
                    "size_bytes": 5678
                }
            ],
            "next_page_token": "xyz789"
        }
        ```

Below is the implementation of the `GET /files` endpoint.  `GetFilesResponse` includes a list of `FileMetadata` objects and an optional `next_page_token` for pagination. `GetFilesQueryParams` defines the query parameters for pagination, including `page_size`, `directory`, and `page_token`. The endpoint fetches files from S3 using the `fetch_s3_objects_metadata` or `fetch_s3_objects_using_page_token` functions, depending on whether a page token is provided. It then converts the fetched file metadata into `FileMetadata` objects and returns them in the response using the `GetFilesResponse` model.

We use `Depends()` to automatically parse and validate the query parameters using FastAPI's dependency injection system against the `GetFilesQueryParams` model.

  - FastAPI automatically converts URL query parameters to the appropriate types defined in the model. Ex:
    - `page_size` will be converted from **string** to **int** automatically.

  - `Depends()` ensures the defaults values from the pydantic model are used when parameters are not provided in the request.

  - Query parameters and their types are clearly **documented** in the Swagger UI and OpenAPI schema generated by FastAPI.
    - Example:
          ```
          GET /files                     → Uses defaults (page_size=10, directory="")
          GET /files?page_size=20        → Uses page_size=20 with other defaults
          GET /files?directory=foo/bar   → Lists files in foo/bar directory
          ```

  - Without `Depends()`, we would have to **manually** parse and validate query parameters, which is error-prone and less efficient.
      - Example:
        ```python
        @APP.get("/files")
        async def list_files(
            page_size: int = 10,
            directory: str = "",
            page_token: Optional[str] = None
        ) -> GetFilesResponse:
            # Manual validation would be needed here
            if page_size <= 0:
                raise HTTPException(status_code=400, detail="Invalid page size")
        ```


```python
# read (cRud)
class FileMetadata(BaseModel):
    file_path: str
    last_modified: datetime
    size_bytes: int

# read (cRud)
class GetFilesResponse(BaseModel):
    files: List[FileMetadata]
    next_page_token: Optional[str]

# read (cRud)
class GetFilesQueryParams(BaseModel):
    page_size: int = 10
    directory: Optional[str] = ""
    page_token: Optional[str] = None


@APP.get("/files")
async def list_files(
    query_params: GetFilesQueryParams = Depends(),  # noqa: B008
) -> GetFilesResponse:
    """List files with pagination."""
    # Validate page size
    if query_params.page_token:
        # If a page token is provided, fetch the next page of files
        files, next_page_token = fetch_s3_objects_using_page_token(
            bucket_name=S3_BUCKET_NAME,
            continuation_token=query_params.page_token,
            max_keys=query_params.page_size,
        )
    else:
        # If no page token is provided, fetch the first page of files
        files, next_page_token = fetch_s3_objects_metadata(
            bucket_name=S3_BUCKET_NAME,
            prefix=query_params.directory,
            max_keys=query_params.page_size,
        )

    # Convert the list of files to FileMetadata objects
    file_metadata_objs = [
        FileMetadata(
            file_path=f"{item['Key']}",
            last_modified=item["LastModified"],
            size_bytes=item["Size"],
        )
        for item in files
    ]

    return GetFilesResponse(
        files=file_metadata_objs, 
        next_page_token=next_page_token if next_page_token else None
        )
```

### 3.3 Get File
To retrieve a specific file from S3, we will use the `GET` method. This method fetches the file from the specified path in S3 and returns it to the client.

- Endpoint: `/files/{file_path:path}`
    - Method: `GET`

- Request
    - Path Parameter: `file_path` (string, required) - The path of the file to retrieve from S3.
    - Query Parameters: None
    - Request Body: None
    - Notable Request Headers: None
    - Example Request:
        ```http
        GET /files/my_folder/my_file.txt
        ```

- Response
    - Status Codes:
        - `200 OK` - If the file was successfully retrieved.
    - Notable Response Headers:
        - `Content-Type` (string) - The MIME type of the file being returned (e.g., `text/plain`, `image/jpeg`).
        - `Content-Length` (integer) - The size of the file in bytes.
    - Response Payload: The file content as a binary stream.
    - Example Response:
        ```http
        HTTP/1.1 200 OK
        Content-Type: text/plain
        (file content here)
        ```

We use `StreamingResponse` to stream the file content directly from S3 to the client. This allows **large** files to be sent efficiently without loading them fully into **memory**. 

The `StreamingResponse` will automatically set the `Content-Type` header based on the file's `MIME` type, so the browser knows how to handle it. For example, if it's a text file, it will be displayed as text. If it's an image, it will be displayed as an image. If it's a PDF, it will be displayed as a PDF document.


```python
from fastapi.responses import StreamingResponse


@APP.get("/files/{file_path:path}")
async def get_file(
    file_path: str,
) -> StreamingResponse:
    """Retrieve a file."""
    # Fetch the file from S3
    # Note: file_path is the full path in S3, including any directories
    get_object_response = fetch_s3_object(S3_BUCKET_NAME, 
    object_key=file_path)

    # Return the file as a streaming response
    # This allows large files to be sent without loading them fully into memory
    return StreamingResponse(
        content=get_object_response["Body"],
        media_type=get_object_response["ContentType"],
    )
```

### 3.4 Get File Metadata
To retrieve metadata for a specific file in S3, we will use the `HEAD` method. This method fetches metadata about the file without transferring the file content itself. This is useful for checking properties like size, type, and last modified date without downloading the entire file.

- Endpoint: `/files/{file_path:path}`
    - Method: `HEAD`

- Request
    - Path Parameter: `file_path` (string, required) - The path of the file to retrieve metadata for.
    - Query Parameters: None
    - Request Body: None
    - Notable Request Headers: None
    - Example Request:
        ```http
        HEAD /files/my_folder/my_file.txt   
        ```

- Response
    - Status Codes:
        - `200 OK` - If the file metadata was successfully retrieved.
        - `404 Not Found` - If the file does not exist in S3.
    - Notable Response Headers:
        - `Content-Type` (string) - The MIME type of the file (e.g, `text/plain`, `image/jpeg`).
        - `Content-Length` (integer) - The size of the file in bytes.
        - `Last-Modified` (string, ISO 8601 format) - The last modified timestamp of the file.
    - Response Payload: None
    - Example Response:
        ```http
        HTTP/1.1 200 OK
        Content-Type: text/plain
        Content-Length: 1234
        Last-Modified: Wed, 01 Oct 2023 12:00:00 GMT
        ```

Note : By convention, `HEAD` requests MUST NOT return a body in the response. The response should only contain headers with metadata about the file.
We use the `fetch_s3_object` function to retrieve the file metadata from S3.

```python
@APP.head("/files/{file_path:path}")
async def get_file_metadata(file_path: str, response: Response) -> Response:
    """Retrieve file metadata.

    Note: by convention, HEAD requests MUST NOT return a body in the response.
    """
    # Fetch the file metadata from S3
    get_object_response = fetch_s3_object(S3_BUCKET_NAME, object_key=file_path)

    # Set the response headers based on the S3 object metadata
    response.headers["Content-Type"] = get_object_response["ContentType"]
    response.headers["Content-Length"] = str(get_object_response["ContentLength"])
    response.headers["Last-Modified"] = get_object_response["LastModified"].strftime("%a, %d %b %Y %H:%M:%S GMT")

    # Set the status code to 200 OK
    # HEAD requests do not return a body, so we just set the status code and headers
    response.status_code = status.HTTP_200_OK
    
    return response

```

### 3.5 Delete File
To delete a specific file from S3, we will use the `DELETE` method. This method removes the file from the specified path in S3.


- Endpoint: `/files/{file_path:path}`
    - Method: `DELETE`

- Request
    - Path Parameter: `file_path` (string, required) - The path of the file to delete from S3.
    - Query Parameters: None
    - Request Body: None
    - Notable Request Headers: None
    - Example Request:
        ```http
        DELETE /files/my_folder/my_file.txt
        ``` 

- Response
    - Status Codes:
        - `204 No Content` - If the file was successfully deleted.
        - `404 Not Found` - If the file does not exist in S3.
    - Notable Response Headers: None
    - Response Payload: None
    - Example Response: 
        ```http
        HTTP/1.1 204 No Content
        ```

Note: By convention, `DELETE` requests MUST NOT return a body in the response. The response should only indicate the success of the operation with a status code.

We use the `delete_s3_object` function to delete the file from S3. The response status code is set to `204 No Content`, indicating that the request was successful and there is no content to return in the response body.



```python
@APP.delete("/files/{file_path:path}")
async def delete_file(
    file_path: str,
    response: Response,
) -> Response:
    """Delete a file.

    NOTE: DELETE requests MUST NOT return a body in the response."""
    # Delete the file from S3
    delete_s3_object(
        bucket_name=S3_BUCKET_NAME,
        object_key=file_path,
    )
    # Set the response status code to 204 No Content
    # This indicates that the request was successful and there is no content to return
    response.status_code = status.HTTP_204_NO_CONTENT
    
    return response
```





-------------------------------------------

## 4. Twelve-Factor App

### Settings

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Settings for the files API.

    Attributes:
        s3_bucket_name: The name of the S3 bucket to use for storing files.
        model_config: Configuration for the settings.
    """

    s3_bucket_name: str = Field(...)
    model_config = SettingsConfigDict(case_sensitive=False)
```


### Routes

```python
@ROUTER.get("/files")
async def list_files(
    request: Request, # This parameter allows the route handler to receive the current HTTP request object, which provides access to information about the request and the application state (e.g., app.state.settings). FastAPI automatically injects this object when the endpoint is called.
    query_params: GetFilesQueryParams = Depends(),  # noqa: B008
) -> GetFilesResponse:
    ...
    settings: Settings = request.app.state.settings
    s3_bucket_name = settings.s3_bucket_name
    ...
```


### Schemas



### Main

```python
def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and return the FastAPI application instance."""
    settings = settings or Settings()
    app = FastAPI()
    app.state.settings = settings
    app.include_router(ROUTER)
    return app

```

```bash
function run-mock {
    python -m moto.server -p 5000 &

    export AWS_ENDPOINT_URL="http://localhost:5000"
    export AWS_ACCESS_KEY_ID="mock"
    export AWS_SECRET_ACCESS_KEY="mock"
    export S3_BUCKET_NAME="some-bucket"

    # crete a bucket using mocked aws server
    aws s3 mb s3://"$S3_BUCKET_NAME"

    uvicorn src.files_api.main:create_app --reload
}
```

```bash
function run {
    AWS_PROFILE=cloud-course S3_BUCKET_NAME="$S3_BUCKET_NAME" uvicorn src.files_api.main:create_app --reload
}
```




-------------------------------------------

## 5. Error Handling


Informational responses (100 – 199)
Successful responses (200 – 299)
Redirection messages (300 – 399)
Client error responses (400 – 499)
Server error responses (500 – 599)






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


### Query vs Path Parameters
In RESTful APIs, query parameters and path parameters serve different purposes:
- **Path Parameters** are part of the URL path and are used to identify a specific resource or resource collection. They are typically used for hierarchical data structures. For example, in the URL `/files/my_folder/my_file.txt`, `my_folder` and `my_file.txt` are path parameters. They are required to uniquely identify the resource being accessed.

```python
def get_file(file_path: str):
    # file_path is a path parameter
    return f"Retrieving file at {file_path}"
```

- **Query Parameters** are appended to the URL after a `?` and are used to filter, sort, or paginate resources. They are optional and can be used to modify the request without changing the resource being accessed. For example, in the URL `/files?directory=my_folder&page_size=10`, `directory` and `page_size` are query parameters. They do not change the resource being accessed but modify how the resource is returned.
  
```python
def list_files(directory: str = "", page_size: int = 10):
    # directory and page_size are query parameters
    return f"Listing files in {directory} with page size {page_size}"
```

## References
1. https://12factor.net/
2. https://docs.pydantic.dev/latest/concepts/pydantic_settings/#usage
3. https://fastapi.tiangolo.com/advanced/settings/

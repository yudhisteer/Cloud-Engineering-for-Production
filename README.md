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








-------------------------------------------

## 4. Twelve-Factor App






-------------------------------------------


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


## References
1. https://12factor.net/

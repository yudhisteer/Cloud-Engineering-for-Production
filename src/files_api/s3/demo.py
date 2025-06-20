import boto3

try:
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_s3.type_defs import PutObjectOutputTypeDef
except ImportError:
    print("mypy-boto3-s3 is not installed, skipping type checking")


BUCKET_NAME = "cloud-course-bucket-yuvish"

session: boto3.Session = boto3.Session(profile_name="cloud-course")
s3: "S3Client" = session.client("s3")

# wrie a file to the s3 bucket with content "Hello, World!"
response: "PutObjectOutputTypeDef" = s3.put_object(
    Bucket=BUCKET_NAME, 
    Key="folder/hello.txt", 
    Body="Hello, World!",
    ContentType="text/plain"
    )
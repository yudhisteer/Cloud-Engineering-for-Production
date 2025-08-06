from pydantic import BaseModel, Field
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
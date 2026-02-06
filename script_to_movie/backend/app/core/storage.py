import boto3
from botocore.exceptions import ClientError

from app.config import get_settings

settings = get_settings()


class StorageClient:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client(
                "s3",
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region,
            )
        return self._client

    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        try:
            self.client.put_object(
                Bucket=settings.s3_bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
            return f"https://{settings.s3_bucket}.s3.{settings.aws_region}.amazonaws.com/{key}"
        except ClientError as e:
            raise RuntimeError(f"Failed to upload to S3: {e}")

    async def download(self, key: str) -> bytes:
        try:
            response = self.client.get_object(Bucket=settings.s3_bucket, Key=key)
            return response["Body"].read()
        except ClientError as e:
            raise RuntimeError(f"Failed to download from S3: {e}")

    async def delete(self, key: str) -> None:
        try:
            self.client.delete_object(Bucket=settings.s3_bucket, Key=key)
        except ClientError as e:
            raise RuntimeError(f"Failed to delete from S3: {e}")

    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        try:
            return self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.s3_bucket, "Key": key},
                ExpiresIn=expires_in,
            )
        except ClientError as e:
            raise RuntimeError(f"Failed to generate presigned URL: {e}")


storage_client = StorageClient()

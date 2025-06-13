from typing import Any

from botocore.client import BaseClient
from botocore.exceptions import ClientError
from loguru import logger

from utils.storage import get_s3_client


class S3MultipartService:
    def __init__(
        self, bucket_name: str, object_key: str, s3_client: BaseClient | None = None
    ):
        self.bucket_name = bucket_name
        self.object_key = object_key
        self.s3_client = s3_client or get_s3_client()
        self.upload_id: str | None = None
        self.parts: list[dict[str, Any]] = []
        self.logger = logger

        self._initialize_mpu_internal()

    def _initialize_mpu_internal(self) -> None:
        mpu_params = {
            "Bucket": self.bucket_name,
            "Key": self.object_key,
            "ContentType": "application/json",
        }
        mpu = self.s3_client.create_multipart_upload(**mpu_params)
        self.upload_id = mpu["UploadId"]
        self._is_mpu_initialized = True
        self.logger.info(
            f"MPU initialized: {self.upload_id} for s3://{self.bucket_name}/{self.object_key}"
        )

    def upload_part(self, part_number: int, body_content: bytes) -> bool:
        try:
            response = self.s3_client.upload_part(
                Bucket=self.bucket_name,
                Key=self.object_key,
                UploadId=self.upload_id,
                PartNumber=part_number,
                Body=body_content,
            )
            self.parts.append({"PartNumber": part_number, "ETag": response["ETag"]})
            self.logger.info(
                f"Uploaded part {part_number} (size: {len(body_content)}) for {self.object_key}"
            )
            return True
        except ClientError as e:
            self.logger.error(
                f"Failed to upload part {part_number} for {self.object_key}. Error: {e}",
                exc_info=True,
            )
            return False

    def complete_mpu(self) -> bool:
        if not self.parts:
            self.logger.warning(
                f"No S3 parts staged for {self.object_key}. Aborting MPU."
            )
            self.abort_mpu("No S3 parts to complete MPU.")
            return False
        try:
            self.s3_client.complete_multipart_upload(
                Bucket=self.bucket_name,
                Key=self.object_key,
                UploadId=self.upload_id,
                MultipartUpload={"Parts": self.parts},
            )
            self.logger.info(
                f"MPU completed for s3://{self.bucket_name}/{self.object_key}"
            )
            return True
        except ClientError as e:
            self.logger.error(
                f"S3 MPU completion failed for {self.object_key}. Error: {e}",
                exc_info=True,
            )
            self.abort_mpu(f"Failed to complete MPU: {e}")
            return False

    def abort_mpu(self, reason: str = "Error during processing"):
        if self.upload_id:
            try:
                self.logger.warning(
                    f"Aborting MPU {self.upload_id} for {self.object_key}. Reason: {reason}"
                )
                self.s3_client.abort_multipart_upload(
                    Bucket=self.bucket_name,
                    Key=self.object_key,
                    UploadId=self.upload_id,
                )
            except ClientError as abort_e:
                self.logger.error(
                    f"Failed to abort MPU {self.upload_id} for {self.object_key}. Error: {abort_e}",
                    exc_info=True,
                )
        else:
            self.logger.warning(
                f"Attempted to abort MPU for {self.object_key}, but no UploadId was set (MPU likely not initialized)."
            )

        self.upload_id = None
        self.parts = []

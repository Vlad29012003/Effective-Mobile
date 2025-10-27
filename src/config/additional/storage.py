from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class CustomS3Storage(S3Boto3Storage):
    def url(self, name, parameters=None, expire=None, http_method=None):
        original_url = super().url(name, parameters=parameters, expire=expire, http_method=http_method)
        return original_url.replace(settings.MINIO_ENDPOINT, settings.MINIO_PUBLIC_ENDPOINT)

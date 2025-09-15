from drf_spectacular.utils import extend_schema


class BaseViewSchema:
    schema: dict = {}

    @classmethod
    def get_schema(cls):
        return extend_schema(**cls.schema)

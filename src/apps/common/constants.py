from enum import Enum

GroupPermission = dict[str, list[str]]


class BaseEnum(Enum):
    @classmethod
    def values(cls) -> list:
        return [item.value for item in cls]

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value


class AppPrefixes(BaseEnum):
    """
    Application prefixes for permission system.
    Centralized storage to avoid hardcoded strings.
    """

    BLOG = "blog"
    USER = "user"
    ADMIN = "admin"
    COMMON = "common"

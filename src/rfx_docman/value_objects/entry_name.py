import re
from dataclasses import dataclass
from typing import ClassVar

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema, PydanticCustomError

_NAME_MAX_LEN = 255
_TAG_MAX_LEN = 100

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


def _pydantic_vo_schema(cls: type) -> core_schema.CoreSchema:
    """Shared Pydantic schema builder for str-based VO dataclasses."""

    def validate(value: str) -> object:
        try:
            return cls(value)
        except ValueError as exc:
            raise PydanticCustomError(
                "invalid_name", "{message}", {"message": str(exc)}
            ) from exc

    return core_schema.chain_schema(
        [
            core_schema.str_schema(),
            core_schema.no_info_plain_validator_function(validate),
        ],
        serialization=core_schema.plain_serializer_function_ser_schema(str),
    )


@dataclass(frozen=True)
class EntryName:
    """File / document name: no slashes, no control chars, max 255 chars."""

    value: str

    def __post_init__(self):
        name = self.value.strip()

        if not name:
            raise ValueError("Name cannot be empty")
        if len(name) > _NAME_MAX_LEN:
            raise ValueError(f"Name cannot exceed {_NAME_MAX_LEN} characters")
        if "/" in name or "\\" in name:
            raise ValueError("Name cannot contain '/' or '\\'")
        if _CONTROL_CHARS.search(name):
            raise ValueError("Name contains control characters")

        object.__setattr__(self, "value", name)

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"EntryName({self.value!r})"

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: type, handler: GetCoreSchemaHandler
    ):
        return _pydantic_vo_schema(cls)


@dataclass(frozen=True)
class FolderName:
    """Folder segment: letters, digits, hyphens, underscores, spaces only."""

    value: str

    _ALLOWED: ClassVar[re.Pattern] = re.compile(r"^[a-zA-Z0-9_\- ]+$")

    def __post_init__(self):
        name = self.value.strip()

        if not name:
            raise ValueError("Folder name cannot be empty")
        if len(name) > _NAME_MAX_LEN:
            raise ValueError(f"Folder name cannot exceed {_NAME_MAX_LEN} characters")
        if not self._ALLOWED.fullmatch(name):
            raise ValueError(
                "Folder name may only contain letters, digits, hyphens, underscores and spaces"
            )

        object.__setattr__(self, "value", name)

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"FolderName({self.value!r})"

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: type, handler: GetCoreSchemaHandler
    ):
        return _pydantic_vo_schema(cls)


@dataclass(frozen=True)
class TagName:
    """Tag name: non-empty string, max 100 chars."""

    value: str

    def __post_init__(self):
        name = self.value.strip()

        if not name:
            raise ValueError("Tag name cannot be empty")
        if len(name) > _TAG_MAX_LEN:
            raise ValueError(f"Tag name cannot exceed {_TAG_MAX_LEN} characters")

        object.__setattr__(self, "value", name)

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"TagName({self.value!r})"

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: type, handler: GetCoreSchemaHandler
    ):
        return _pydantic_vo_schema(cls)

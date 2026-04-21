import re
from dataclasses import dataclass
from typing import ClassVar

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema, PydanticCustomError


@dataclass(frozen=True)
class CodeBase:
    value: str

    PATTERN: ClassVar[re.Pattern] = re.compile(r"(?!)")
    NAME: ClassVar[str] = "Code"
    EXAMPLE: ClassVar[str] = ""

    def __post_init__(self):
        if not isinstance(self.value, str):
            raise ValueError(f"{self.NAME} must be a string")

        normalized = self.value.strip().upper()
        object.__setattr__(self, "value", normalized)

        if not self.PATTERN.fullmatch(normalized):
            raise ValueError(
                f"{self.NAME} must match {self.PATTERN.pattern} "
                f"(example: {self.EXAMPLE})"
            )

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.value!r})"

    # --- Pydantic v2 integration ---
    @classmethod
    def _pydantic_validate(cls, value: str) -> "CodeBase":
        try:
            return cls(value)
        except (ValueError, TypeError) as exc:
            raise PydanticCustomError(
                "invalid_code", "{message}", {"message": str(exc)}
            ) from exc

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: type,
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls._pydantic_validate),
            ],
            serialization=core_schema.plain_serializer_function_ser_schema(str),
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        json_schema = handler(core_schema)
        json_schema.update(
            {
                "type": "string",
                "pattern": cls.PATTERN.pattern,
                "examples": [cls.EXAMPLE],
                "description": f"{cls.NAME} code (example: {cls.EXAMPLE})",
            }
        )
        return json_schema


@dataclass(frozen=True)
class ShelfCode(CodeBase):
    PATTERN: ClassVar[re.Pattern] = re.compile(r"^[A-Z]$")
    NAME: ClassVar[str] = "Shelf"
    EXAMPLE: ClassVar[str] = "A"


@dataclass(frozen=True)
class CategoryCode(CodeBase):
    PATTERN: ClassVar[re.Pattern] = re.compile(r"^[A-Z][0-9]{2}$")
    NAME: ClassVar[str] = "Category"
    EXAMPLE: ClassVar[str] = "A01"

    def belongs_to(self, shelf: ShelfCode) -> bool:
        return self.value[0] == str(shelf)


@dataclass(frozen=True)
class CabinetCode(CodeBase):
    PATTERN: ClassVar[re.Pattern] = re.compile(r"^[A-Z][0-9]{2}-[0-9]{3}$")
    NAME: ClassVar[str] = "Cabinet"
    EXAMPLE: ClassVar[str] = "A01-001"

    def belongs_to(self, category: CategoryCode) -> bool:
        return self.value.startswith(f"{category}-")

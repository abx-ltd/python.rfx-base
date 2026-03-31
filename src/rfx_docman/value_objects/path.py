import posixpath
from dataclasses import dataclass
from typing import List

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema, PydanticCustomError

from .entry_name import FolderName, InvalidNameError


@dataclass(frozen=True)
class Path:
    """Slash-delimited, normalised cabinet path. Empty string = root.

    Prefer `from_string()` / `root()` for external input.
    """

    value: str

    def __post_init__(self):
        object.__setattr__(self, "value", self._normalize(self.value))

    @staticmethod
    def root() -> "Path":
        return Path("")

    @staticmethod
    def from_string(path: str) -> "Path":
        return Path(path)

    @staticmethod
    def _normalize(path: str) -> str:
        if not path or not path.strip("/"):
            return ""

        cleaned = posixpath.normpath(path).strip("/")
        if cleaned.startswith(".."):
            raise InvalidNameError("Path traversal is not allowed")
        segments: List[str] = [str(FolderName(seg)) for seg in cleaned.split("/")]
        return "/".join(segments)

    def join(self, name: str) -> "Path":
        """Append name to this path. Input is validated via Path normalization."""
        if not self.value:
            return Path(name)
        return Path(f"{self.value}/{name}")

    def parent(self) -> "Path":
        """Return the parent path, or root if already at root."""
        if "/" not in self.value:
            return Path.root()
        return Path(self.value.rsplit("/", 1)[0])

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"Path({self.value!r})"

    # --- Pydantic v2 integration ---

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: type,
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        def validate(value: str) -> "Path":
            try:
                return cls.from_string(value)
            except InvalidNameError as exc:
                raise PydanticCustomError(
                    "invalid_path", "{message}", {"message": str(exc)}
                ) from exc

        return core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(validate),
            ],
            serialization=core_schema.plain_serializer_function_ser_schema(str),
        )

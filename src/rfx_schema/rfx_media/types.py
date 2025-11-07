"""
RFX Media Domain Enum Definitions (Schema Layer)

Lightweight replicas of the enums used in ``lib.fluvius.media.model`` so the
schema package can be imported without touching the runtime connector code.
"""

from enum import Enum


class FsSpecCompressionMethod(Enum):
    BZ2 = "bz2"
    GZIP = "gzip"
    LZ4 = "lz4"
    LZMA = "lzma"
    SNAPPY = "snappy"
    XZ = "xz"
    ZIP = "zip"
    ZSTD = "zstd"


class FsSpecFsType(Enum):
    S3 = "s3"

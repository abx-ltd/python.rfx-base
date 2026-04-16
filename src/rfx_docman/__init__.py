"""RFX Docman"""

from ._meta import config, logger
from .domain import RFXDocmanDomain

from .query import RFXDocmanQueryManager
from . import command  # noqa: F401
from .endpoints import configure_docman_endpoints

__all__ = [
    "config",
    "logger",
    "RFXDocmanDomain",
    "RFXDocmanQueryManager",
    "configure_docman_endpoints",
]

from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .. import create_base_model, logger
from rfx_base import config

Base = create_base_model(config.RFX_DISCUSS_SCHEMA)


class TableBase(Base):
    __abstract__ = True
    _realm: Mapped[Optional[str]] = mapped_column(String(255))


SCHEMA = config.RFX_DISCUSS_SCHEMA

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from . import TableBase, SCHEMA


class HatchetWorkflowRunView(TableBase):
    __tablename__ = "_hatchet_workflow_run"
    __table_args__ = {"schema": SCHEMA, "info": {"is_view": True}}

    workflow_name: Mapped[str] = mapped_column(String)
    workflow_run_id: Mapped[str] = mapped_column(String)
    labels: Mapped[Optional[dict]] = mapped_column(JSONB)
    args: Mapped[Optional[dict]] = mapped_column(JSONB)
    kwargs: Mapped[Optional[dict]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String)
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    result: Mapped[Optional[dict]] = mapped_column(JSONB)
    err_message: Mapped[Optional[str]] = mapped_column(String)
    err_trace: Mapped[Optional[str]] = mapped_column(String)

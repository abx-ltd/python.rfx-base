#!/usr/bin/env python3
"""
CLI entry point for the TTP manager module

Usage:
    python -m ttp_manager import-fhir --source synthea_florida
    python -m ttp_manager import-fhir --source synthea_texas --limit 100
"""

from flctl.entrypoint import cli
from . import entrypoint as _entrypoint  # noqa: F401 — side effect: register `rfx` on `cli`

cli()

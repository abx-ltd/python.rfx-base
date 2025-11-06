#!/usr/bin/env python3
"""
CLI entry point for the TTP manager module

Usage:
    python -m ttp_manager import-fhir --source synthea_florida
    python -m ttp_manager import-fhir --source synthea_texas --limit 100
"""

from fluvius.manager import fluvius_manager
from .entrypoint import rfx_manager

fluvius_manager.add_command(rfx_manager)
fluvius_manager()

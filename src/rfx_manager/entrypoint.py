import click
from fluvius.manager import fluvius_manager


@fluvius_manager.group(name="rfx")
def rfx_manager():
    """RFX Manager Commands."""

    pass

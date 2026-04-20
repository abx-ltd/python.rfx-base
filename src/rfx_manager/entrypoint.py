import click
from flctl.entrypoint import cli


@cli.group(name="rfx")
def rfx_manager():
    """RFX Manager Commands."""

    pass

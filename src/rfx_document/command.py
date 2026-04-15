from fluvius.data import serialize_mapping

from .domain import RFXDocumentDomain
from . import datadef

processor = RFXDocumentDomain.command_processor
Command = RFXDocumentDomain.Command

class CreateReal(Command):
    """"Create a realm ."""

    Data = datadef.CreateRealPayload

    class Meta:
        key = "create-realm"
        resources = ("realm",)
        tags = ["document", "create","realm"]
        auth_required = True
        resource_init = True

    async def _process(self, agg, stm, payload):
        result = await agg.create_real(payload)
        yield agg.create_response(serialize_mapping(result), _type="document-response")


class UpdateRealm(Command):
    """Update a realm."""

    Data = datadef.UpdateRealPayload

    class Meta:
        key = "update-realm"
        resources = ("realm",)
        tags = ["document", "update", "realm"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        result = await agg.update_realm(payload)
        yield agg.create_response(serialize_mapping(result), _type="document-response")


class RemoveRealm(Command):
    """Remove a realm."""

    class Meta:
        key = "remove-realm"
        resources = ("realm",)
        tags = ["document", "remove", "realm"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        await agg.remove_realm()


class CreateShelf(Command):
    """Create a shelf."""

    Data = datadef.CreateShelfPayload

    class Meta:
        key = "create-shelf"
        resources = ("shelf",)
        tags = ["document", "create", "shelf"]
        auth_required = True
        resource_init = True

    async def _process(self, agg, stm, payload):
        result = await agg.create_shelf(payload)
        yield agg.create_response(serialize_mapping(result), _type="document-response")


class UpdateShelf(Command):
    """Update a shelf."""

    Data = datadef.UpdateShelfPayload

    class Meta:
        key = "update-shelf"
        resources = ("shelf",)
        tags = ["document", "update", "shelf"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        result = await agg.update_shelf(payload)
        yield agg.create_response(serialize_mapping(result), _type="document-response")


class RemoveShelf(Command):
    """Remove a shelf."""

    class Meta:
        key = "remove-shelf"
        resources = ("shelf",)
        tags = ["document", "remove", "shelf"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        await agg.remove_shelf()



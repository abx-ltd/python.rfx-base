from fluvius.data import serialize_mapping

from .domain import RFXDocumentDomain
from . import datadef

processor = RFXDocumentDomain.command_processor
Command = RFXDocumentDomain.Command


class CreateRealm(Command):
    """ "Create a realm ."""

    Data = datadef.CreateRealmPayload

    class Meta:
        key = "create-realm"
        resources = ("realm",)
        tags = ["document", "create", "realm"]
        auth_required = True
        resource_init = True

    async def _process(self, agg, stm, payload):
        result = await agg.create_real(payload)
        yield agg.create_response(serialize_mapping(result), _type="document-response")


class UpdateRealm(Command):
    """Update a realm."""

    Data = datadef.UpdateRealmPayload

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
        resources = ("realm",)
        tags = ["document", "create", "shelf"]
        auth_required = True

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


class CreateCategory(Command):
    """Create a category."""

    Data = datadef.CreateCategoryPayload

    class Meta:
        key = "create-category"
        resources = ("shelf",)
        tags = ["document", "create", "category"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        result = await agg.create_category(payload)
        yield agg.create_response(serialize_mapping(result), _type="document-response")


class UpdateCategory(Command):
    """Update a category."""

    Data = datadef.UpdateCategoryPayload

    class Meta:
        key = "update-category"
        resources = ("category",)
        tags = ["document", "update", "category"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        result = await agg.update_category(payload)
        yield agg.create_response(serialize_mapping(result), _type="document-response")


class RemoveCategory(Command):
    """Remove a category."""

    class Meta:
        key = "remove-category"
        resources = ("category",)
        tags = ["document", "remove", "category"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        await agg.remove_category()


class CreateCabinet(Command):
    """Create a cabinet."""

    Data = datadef.CreateCabinetPayload

    class Meta:
        key = "create-cabinet"
        resources = ("category",)
        tags = ["document", "create", "cabinet"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        result = await agg.create_cabinet(payload)
        yield agg.create_response(serialize_mapping(result), _type="document-response")


class UpdateCabinet(Command):
    """Update a cabinet."""

    Data = datadef.UpdateCabinetPayload

    class Meta:
        key = "update-cabinet"
        resources = ("cabinet",)
        tags = ["document", "update", "cabinet"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        result = await agg.update_cabinet(payload)
        yield agg.create_response(serialize_mapping(result), _type="document-response")


class RemoveCabinet(Command):
    """Remove a cabinet."""

    class Meta:
        key = "remove-cabinet"
        resources = ("cabinet",)
        tags = ["document", "remove", "cabinet"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        await agg.remove_cabinet()

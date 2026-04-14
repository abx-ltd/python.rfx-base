from fluvius.data import serialize_mapping

from .domain import RFXDocmanDomain
from . import datadef

processor = RFXDocmanDomain.command_processor
Command = RFXDocmanDomain.Command


class CreateRealm(Command):
    """Create a realm."""

    Data = datadef.CreateRealmPayload

    class Meta:
        key = "create-realm"
        resources = ("realm",)
        tags = ["docman", "create", "realm"]
        auth_required = True
        resource_init = True

    async def _process(self, agg, stm, payload):
        result = await agg.create_realm(payload)
        yield agg.create_response(serialize_mapping(result), _type="realm-response")


class UpdateRealm(Command):
    """Update a realm."""

    Data = datadef.UpdateRealmPayload

    class Meta:
        key = "update-realm"
        resources = ("realm",)
        tags = ["docman", "update", "realm"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        result = await agg.update_realm(payload)
        yield agg.create_response(serialize_mapping(result), _type="realm-response")


class RemoveRealm(Command):
    """Soft-delete a realm."""

    class Meta:
        key = "remove-realm"
        resources = ("realm",)
        tags = ["docman", "remove", "realm"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        await agg.remove_realm()


class CreateRealmMeta(Command):
    """Create a realm meta."""

    Data = datadef.CreateRealmMetaPayload

    class Meta:
        key = "create-realm-meta"
        resources = ("realm",)
        tags = ["docman", "create", "realm-meta"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        result = await agg.create_realm_meta(payload)
        yield agg.create_response(
            serialize_mapping(result), _type="realm-meta-response"
        )


class UpdateRealmMeta(Command):
    """Update a realm meta."""

    Data = datadef.UpdateRealmMetaPayload

    class Meta:
        key = "update-realm-meta"
        resources = ("realm_meta",)
        tags = ["docman", "update", "realm_meta"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        result = await agg.update_realm_meta(payload)
        yield agg.create_response(
            serialize_mapping(result), _type="realm-meta-response"
        )


class RemoveRealmMeta(Command):
    """Soft-delete a realm metadata record."""

    class Meta:
        key = "remove-realm-meta"
        resources = ("realm_meta",)
        tags = ["docman", "remove", "realm_meta"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        await agg.remove_realm_meta()


class CreateShelf(Command):
    """Create a shelf."""

    Data = datadef.CreateShelfPayload

    class Meta:
        key = "create-shelf"
        resources = ("realm",)
        tags = ["docman", "create", "shelf"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        result = await agg.create_shelf(payload)
        yield agg.create_response(serialize_mapping(result), _type="shelf-response")


class UpdateShelf(Command):
    """Update a shelf."""

    Data = datadef.UpdateShelfPayload

    class Meta:
        key = "update-shelf"
        resources = ("shelf",)
        tags = ["docman", "update", "shelf"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        result = await agg.update_shelf(payload)
        yield agg.create_response(serialize_mapping(result), _type="shelf-response")


class RemoveShelf(Command):
    """Soft-delete a shelf."""

    class Meta:
        key = "remove-shelf"
        resources = ("shelf",)
        tags = ["docman", "remove", "shelf"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        await agg.remove_shelf()


class CreateCategory(Command):
    """Create a category."""

    Data = datadef.CreateCategoryPayload

    class Meta:
        key = "create-category"
        resources = ("shelf",)
        tags = ["docman", "create", "category"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        result = await agg.create_category(payload)
        yield agg.create_response(serialize_mapping(result), _type="category-response")


class UpdateCategory(Command):
    """Update a category."""

    Data = datadef.UpdateCategoryPayload

    class Meta:
        key = "update-category"
        resources = ("category",)
        tags = ["docman", "update", "category"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        result = await agg.update_category(payload)
        yield agg.create_response(serialize_mapping(result), _type="category-response")


class RemoveCategory(Command):
    """Soft-delete a category."""

    class Meta:
        key = "remove-category"
        resources = ("category",)
        tags = ["docman", "remove", "category"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        await agg.remove_category()


class CreateCabinet(Command):
    """Create a cabinet."""

    Data = datadef.CreateCabinetPayload

    class Meta:
        key = "create-cabinet"
        resources = ("category",)
        tags = ["docman", "create", "cabinet"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        result = await agg.create_cabinet(payload)
        yield agg.create_response(serialize_mapping(result), _type="cabinet-response")


class UpdateCabinet(Command):
    """Update a cabinet."""

    Data = datadef.UpdateCabinetPayload

    class Meta:
        key = "update-cabinet"
        resources = ("cabinet",)
        tags = ["docman", "update", "cabinet"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        result = await agg.update_cabinet(payload)
        yield agg.create_response(serialize_mapping(result), _type="cabinet-response")


class RemoveCabinet(Command):
    """Soft-delete a cabinet."""

    class Meta:
        key = "remove-cabinet"
        resources = ("cabinet",)
        tags = ["docman", "remove", "cabinet"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        await agg.remove_cabinet()


class CreateEntry(Command):
    """Create a new entry (file or folder) in a cabinet."""

    Data = datadef.CreateEntryPayload

    class Meta:
        key = "create-entry"
        resources = ("cabinet",)
        tags = ["docman", "entry", "create"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        # Stage 1: delegate creation logic to aggregate.
        result = await agg.create_entry(payload)
        yield agg.create_response(serialize_mapping(result), _type="entry-response")


class UpdateEntry(Command):
    """Update an entry (including move/rename operations)."""

    Data = datadef.UpdateEntryPayload

    class Meta:
        key = "update-entry"
        resources = ("entry",)
        tags = ["docman", "update", "entry"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        result = await agg.update_entry(payload)
        yield agg.create_response(serialize_mapping(result), _type="entry-response")


class RemoveEntry(Command):
    """Soft-delete an entry and let aggregate handle closure cleanup."""

    class Meta:
        key = "remove-entry"
        resources = ("entry",)
        tags = ["docman", "remove", "entry"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        await agg.remove_entry()


class CopyEntry(Command):
    """Copy an entry subtree to destination cabinet/path."""

    Data = datadef.CopyEntryPayload

    class Meta:
        key = "copy-entry"
        resources = ("entry",)
        tags = ["docman", "entry", "copy"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        result = await agg.copy_entry(payload)
        yield agg.create_response(serialize_mapping(result), _type="entry-response")


# =============================================================================
# TAG COMMANDS — globally shared tag CRUD
# =============================================================================


class CreateTag(Command):
    """Create a globally shared tag."""

    Data = datadef.CreateTagPayload

    class Meta:
        key = "create-tag"
        resources = ("tag",)
        tags = ["docman", "create", "tag"]
        auth_required = True
        resource_init = True

    async def _process(self, agg, stm, payload):
        result = await agg.create_tag(payload)
        yield agg.create_response(serialize_mapping(result), _type="tag-response")


class UpdateTag(Command):
    """Update an existing tag."""

    Data = datadef.UpdateTagPayload

    class Meta:
        key = "update-tag"
        resources = ("tag",)
        tags = ["docman", "update", "tag"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        result = await agg.update_tag(payload)
        yield agg.create_response(serialize_mapping(result), _type="tag-response")


class RemoveTag(Command):
    """Soft-delete a tag."""

    class Meta:
        key = "remove-tag"
        resources = ("tag",)
        tags = ["docman", "remove", "tag"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        await agg.remove_tag()


# =============================================================================
# ENTRY TAG COMMANDS — M:N via entry_tag junction
# =============================================================================


class AddEntryTag(Command):
    """Attach a tag to an entry."""

    Data = datadef.AddEntryTagPayload

    class Meta:
        key = "add-entry-tag"
        resources = ("entry",)
        tags = ["docman", "entry", "tag"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        result = await agg.add_entry_tag(payload)
        yield agg.create_response(serialize_mapping(result), _type="entry-tag-response")


class RemoveEntryTag(Command):
    """Detach a tag from an entry."""

    Data = datadef.RemoveEntryTagPayload

    class Meta:
        key = "remove-entry-tag"
        resources = ("entry",)
        tags = ["docman", "entry", "tag"]
        auth_required = True

    async def _process(self, agg, stm, payload):
        await agg.remove_entry_tag(payload)

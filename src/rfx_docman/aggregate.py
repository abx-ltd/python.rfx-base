from asyncpg import UniqueViolationError

from fluvius.domain import Aggregate
from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping, UUID_GENR
from . import helper


class RFXDocmanAggregate(Aggregate):
    """Docman Aggregate - CRUD operations for document items."""

    def _serialize(self, data):
        return serialize_mapping(data)

    async def _ensure_no_children(
        self,
        parent,
        child_type: str,
        where_key: str,
        label: str,
        child_label: str,
    ):
        if await self.statemgr.find_all(child_type, where={where_key: parent._id}):
            raise ValueError(
                f"Cannot remove {label} '{parent.name}' because it still contains {child_label}"
            )

    def _ensure_code_prefix(self, code: str, prefix: str, label: str):
        if not code.startswith(prefix):
            raise ValueError(f"{label} code {code} must start with {prefix}")

    @action("realm-created", resources="realm")
    async def create_realm(self, /, data):
        data = self._serialize(data)
        record = self.init_resource(
            "realm",
            **data,
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        return record

    @action("realm-updated", resources="realm")
    async def update_realm(self, /, data):
        realm = self.rootobj
        updates = self._serialize(data)
        await self.statemgr.update(realm, **updates)
        return await self.statemgr.fetch("realm", realm._id)

    @action("realm-removed", resources="realm")
    async def remove_realm(self, /):
        realm = self.rootobj
        await self._ensure_no_children(realm, "shelf", "realm_id", "realm", "shelves")
        await self.statemgr.invalidate(realm)

    @action("realm-meta-created", resources="realm")
    async def create_realm_meta(self, /, data):
        data = self._serialize(data)
        realm = self.rootobj
        record = self.init_resource(
            "realm_meta",
            {
                **data,
                "realm_id": realm._id,
            },
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        return record

    @action("realm-meta-updated", resources="realm_meta")
    async def update_realm_meta(self, /, data):
        realm_meta = self.rootobj
        updates = self._serialize(data)
        await self.statemgr.update(realm_meta, **updates)
        return await self.statemgr.fetch("realm_meta", realm_meta._id)

    @action("realm-meta-removed", resources="realm_meta")
    async def remove_realm_meta(self, /):
        realm_meta = self.rootobj
        await self.statemgr.invalidate(realm_meta)

    @action("shelf-created", resources="realm")
    async def create_shelf(self, /, data):
        data = self._serialize(data)
        realm = self.rootobj

        record = self.init_resource(
            "shelf",
            {
                **data,
                "realm_id": realm._id,
            },
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        return record

    @action("shelf-updated", resources="shelf")
    async def update_shelf(self, /, data):
        shelf = self.rootobj
        updates = self._serialize(data)
        await self.statemgr.update(shelf, **updates)
        return await self.statemgr.fetch("shelf", shelf._id)

    @action("shelf-removed", resources="shelf")
    async def remove_shelf(self, /):
        shelf = self.rootobj
        await self._ensure_no_children(
            shelf, "category", "shelf_id", "shelf", "categories"
        )
        await self.statemgr.invalidate(shelf)

    @action("category-created", resources="shelf")
    async def create_category(self, /, data):
        data = self._serialize(data)
        shelf = self.rootobj
        code = data["code"]

        self._ensure_code_prefix(code, shelf.code, "Category")

        record = self.init_resource(
            "category",
            {
                **data,
                "realm_id": shelf.realm_id,
                "shelf_id": shelf._id,
            },
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        return record

    @action("category-updated", resources="category")
    async def update_category(self, /, data):
        category = self.rootobj
        updates = self._serialize(data)

        await self.statemgr.update(category, **updates)
        return await self.statemgr.fetch("category", category._id)

    @action("category-removed", resources="category")
    async def remove_category(self, /):
        category = self.rootobj
        await self._ensure_no_children(
            category, "cabinet", "category_id", "category", "cabinets"
        )
        await self.statemgr.invalidate(category)

    @action("cabinet-created", resources="category")
    async def create_cabinet(self, /, data):
        data = self._serialize(data)
        category = self.rootobj
        code = data["code"]
        prefix = f"{category.code}-"

        self._ensure_code_prefix(code, prefix, "Cabinet")

        record = self.init_resource(
            "cabinet",
            {
                **data,
                "realm_id": category.realm_id,
                "category_id": category._id,
            },
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        return record

    @action("cabinet-updated", resources="cabinet")
    async def update_cabinet(self, /, data):
        cabinet = self.rootobj
        updates = self._serialize(data)

        await self.statemgr.update(cabinet, **updates)
        return await self.statemgr.fetch("cabinet", cabinet._id)

    @action("cabinet-removed", resources="cabinet")
    async def remove_cabinet(self, /):
        cabinet = self.rootobj
        await self._ensure_no_children(
            cabinet, "entry", "cabinet_id", "cabinet", "entries"
        )
        await self.statemgr.invalidate(cabinet)

    @action("entry-created", resources="cabinet")
    async def create_entry(self, /, data):
        cabinet = self.rootobj

        data = self._serialize(data)

        record = self.init_resource(
            "entry",
            {**data, "cabinet_id": cabinet._id},
            _id=UUID_GENR(),
        )

        await self.statemgr.insert(record)
        return record

    @action("entry-updated", resources="entry")
    async def update_entry(self, /, data):
        entry = self.rootobj
        updates = self._serialize(data)

        new_path = data.resolve_path(entry)
        old_path = entry.path

        if new_path != old_path:
            await helper.ensure_entry_path_available(
                self.statemgr,
                cabinet_id=entry.cabinet_id,
                path=new_path,
            )
            helper.apply_move_updates(updates, new_path=new_path)

            try:
                await helper.move_folder_descendants(
                    self.statemgr,
                    entry=entry,
                    old_path=old_path,
                    new_path=new_path,
                )
                await self.statemgr.update(entry, **updates)
            except UniqueViolationError:
                raise ValueError(f"An entry already exists at path '{new_path}'")
        else:
            await self.statemgr.update(entry, **updates)

        return await self.statemgr.fetch("entry", entry._id)

    @action("entry-removed", resources="entry")
    async def remove_entry(self, /):
        entry = self.rootobj
        await self.statemgr.invalidate(entry)


    # =========================================================================
    # TAG
    # =========================================================================

    @action("tag-created", resources="realm")
    async def create_tag(self, /, data):
        """Create a globally shared tag in realm"""
        data = self._serialize(data)
        realm = self.rootobj
        tag = self.init_resource(
            "tag",
            {
                **data,
                "realm_id": realm._id,
            },
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(tag)
        return tag

    @action("tag-updated", resources="tag")
    async def update_tag(self, /, data):
        """Update name/color/icon of an existing tag."""
        tag = self.rootobj
        updates = self._serialize(data)
        await self.statemgr.update(tag, **updates)
        return await self.statemgr.fetch("tag", tag._id)

    @action("tag-removed", resources="tag")
    async def remove_tag(self, /):
        """Remove a tag (also cascades through entry_tag if DB supports it)."""
        tag = self.rootobj
        await self.statemgr.invalidate(tag)

    # =========================================================================
    # ENTRY TAG
    # =========================================================================

    @action("entry-tag-added", resources="entry")
    async def add_entry_tag(self, /, data):
        """Attach a tag to an entry via entry_tag."""
        data = self._serialize(data)
        entry = self.rootobj
        tag_id = data["tag_id"]

        tag = await self.statemgr.fetch("tag", tag_id)
        if not tag:
            raise ValueError(f"Tag '{tag_id}' does not exist")

        record = self.init_resource(
            "entry_tag",
            {"entry_id": entry._id, "tag_id": tag_id},
        )
        await self.statemgr.insert(record)
        return record

    @action("entry-tag-removed", resources="entry")
    async def remove_entry_tag(self, /, data):
        """Detach a tag from an entry."""
        data = self._serialize(data)
        entry = self.rootobj
        tag_id = data["tag_id"]

        link = await self.statemgr.exist(
            "entry_tag", where={"entry_id": entry._id, "tag_id": tag_id}
        )
        if not link:
            raise ValueError(f"Tag '{tag_id}' is not attached to this entry")

        await self.statemgr.invalidate(link)

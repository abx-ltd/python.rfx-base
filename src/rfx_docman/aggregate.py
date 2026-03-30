from fluvius.domain import Aggregate
from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping, UUID_GENR
from .types import EntryTypeEnum

class RFXDocmanAggregate(Aggregate):
    """Docman Aggregate - CRUD operations for document items."""

    @action("realm-created", resources="realm")
    async def create_realm(self, /, data):
        data = serialize_mapping(data)
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
        updates = serialize_mapping(data)
        await self.statemgr.update(realm, **updates)
        return await self.statemgr.fetch("realm", realm._id)

    @action("realm-removed", resources="realm")
    async def remove_realm(self, /):
        realm = self.rootobj
        if await self.statemgr.find_all("shelf", where={"realm_id": realm._id}):
            raise ValueError(f"Cannot remove realm '{realm.name}' because it still contains shelves")
        await self.statemgr.invalidate(realm)

    @action("realm-meta-created", resources="realm")
    async def create_realm_meta(self, /, data):
        data = serialize_mapping(data)
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
        updates = serialize_mapping(data)
        await self.statemgr.update(realm_meta, **updates)
        return await self.statemgr.fetch("realm_meta", realm_meta._id)

    @action("realm-meta-removed", resources="realm_meta")
    async def remove_realm_meta(self, /):
        realm_meta = self.rootobj
        await self.statemgr.invalidate(realm_meta)

    @action("shelf-created", resources="realm")
    async def create_shelf(self, /, data):
        data = serialize_mapping(data)
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
        updates = serialize_mapping(data)
        await self.statemgr.update(shelf, **updates)
        return await self.statemgr.fetch("shelf", shelf._id)

    @action("shelf-removed", resources="shelf")
    async def remove_shelf(self, /):
        shelf = self.rootobj
        if await self.statemgr.find_all("category", where={"shelf_id": shelf._id}):
            raise ValueError(f"Cannot remove shelf '{shelf.name}' because it still contains categories")
        await self.statemgr.invalidate(shelf)

    @action("category-created", resources="shelf")
    async def create_category(self, /, data):
        data = serialize_mapping(data)
        shelf = self.rootobj
        code = data["code"]

        if not code.startswith(shelf.code):
            raise ValueError(
                f"Category code {code} must start with shelf code {shelf.code}"
            )
        
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
        updates = serialize_mapping(data)

        if "code" in updates:
            new_code = updates["code"]
            shelf = await self.statemgr.fetch("shelf", category.shelf_id)
            if not new_code.startswith(shelf.code):
                raise ValueError(
                    f"Category code {new_code} must start with shelf code {shelf.code}"
                )

        await self.statemgr.update(category, **updates)
        return await self.statemgr.fetch("category", category._id)

    @action("category-removed", resources="category")
    async def remove_category(self, /):
        category = self.rootobj
        if await self.statemgr.find_all("cabinet", where={"category_id": category._id}):
            raise ValueError(f"Cannot remove category '{category.name}' because it still contains cabinets")
        await self.statemgr.invalidate(category)

    @action("cabinet-created", resources="category")
    async def create_cabinet(self, /, data):
        data = serialize_mapping(data)
        category = self.rootobj
        code = data["code"]
        prefix = f"{category.code}-"

        if not code.startswith(prefix):
            raise ValueError(
                f"Cabinet code {code} must start with category prefix {prefix}"
            )

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
        updates = serialize_mapping(data)

        if "code" in updates:
            new_code = updates["code"]
            category = await self.statemgr.fetch("category", cabinet.category_id)
            prefix = f"{category.code}-"
            if not new_code.startswith(prefix):
                raise ValueError(
                    f"Cabinet code {new_code} must start with category prefix {prefix}"
                )

        await self.statemgr.update(cabinet, **updates)
        return await self.statemgr.fetch("cabinet", cabinet._id)

    @action("cabinet-removed", resources="cabinet")
    async def remove_cabinet(self, /):
        cabinet = self.rootobj
        if await self.statemgr.find_all("entry", where={"cabinet_id": cabinet._id}):
            raise ValueError(f"Cannot remove cabinet '{cabinet.name}' because it still contains entries")
        await self.statemgr.invalidate(cabinet)

    @action("entry-created", resources="cabinet")
    async def create_entry(self, /, data):
        cabinet = self.rootobj
        full_path = data.computed_path

        entry_data = serialize_mapping(data)
        entry_data.update(
            {
                "cabinet_id": cabinet._id,
                "path": full_path,
            }
        )
        entry_data.pop("parent_path", None)

        record = self.init_resource(
            "entry",
            **entry_data,
            _id=UUID_GENR(),
        )

        await self.statemgr.insert(record)
        return record

    @action("entry-updated", resources="entry")
    async def update_entry(self, /, data):
        entry = self.rootobj
        updates = serialize_mapping(data)

        old_type = entry.type
        new_type = data.type
        if new_type is not None and new_type != old_type:
            raise ValueError(
                f"Entry type cannot be changed after creation "
                f"('{old_type.value}' \u2192 '{new_type.value}')"
            )

        # Force folder entries to always have null size/mime_type.
        if old_type == EntryTypeEnum.FOLDER:
            updates["size"] = None
            updates["mime_type"] = None

        # Handle path changes.
        new_path = data.get_computed_path(entry)
        old_path = entry.path

        if new_path != old_path:

            conflict = await self.statemgr.exist(
                "entry",
                where={"cabinet_id": entry.cabinet_id, "path": new_path},
            )
            if conflict:
                raise ValueError(
                    f"An entry already exists at path '{new_path}'"
                )

            updates["path"] = new_path
            updates["name"] = new_path.rsplit("/", 1)[-1]

            if old_type == EntryTypeEnum.FOLDER:
                old_prefix = f"{old_path}/"
                new_prefix = f"{new_path}/"
                await self.statemgr.bulk_update(
                    "entry",
                    where={
                        "cabinet_id": entry.cabinet_id,
                        "path:startswith": old_prefix,
                    },
                    values={
                        "path": {"$reprefix": (old_prefix, new_prefix)},
                        "name": {"$basename_after_reprefix": (old_prefix, new_prefix)},
                    },
                )

        updates.pop("parent_path", None)
        await self.statemgr.update(entry, **updates)
        return await self.statemgr.fetch("entry", entry._id)

    @action("entry-removed", resources="entry")
    async def remove_entry(self, /):
        """
        Soft-delete a single entry (file or FOLDER metadata row).
        """
        entry = self.rootobj
        await self.statemgr.invalidate(entry)

    @action("entry-purged", resources="entry")
    async def purge_entry(self, /):
        """Recursively soft-delete a FOLDER row and all its active descendants.

        """
        entry = self.rootobj
        if entry.type != EntryTypeEnum.FOLDER:
            raise ValueError("purge-entry is only valid for FOLDER entries")

        # Bulk soft-delete all descendants first, then the FOLDER row itself.
        await self.statemgr.invalidate_where(
            "entry",
            {
                "cabinet_id": entry.cabinet_id,
                "path:startswith": f"{entry.path}/",
            },
        )
        await self.statemgr.invalidate(entry)

    # =========================================================================
    # TAG 
    # =========================================================================

    @action("tag-created", resources="realm")
    async def create_tag(self, /, data):
        """Create a globally shared tag in realm
        """
        data = serialize_mapping(data)
        realm = self.rootobj
        tag = self.init_resource(
            "tag",
            {
                **data,
                "realm_id" : realm._id ,
            },
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(tag)
        return tag

    @action("tag-updated", resources="tag")
    async def update_tag(self, /, data):
        """Update name/color/icon of an existing tag."""
        tag = self.rootobj
        updates = serialize_mapping(data)
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
        data = serialize_mapping(data)
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
        data = serialize_mapping(data)
        entry = self.rootobj
        tag_id = data["tag_id"]

        link = await self.statemgr.exist(
            "entry_tag", where={"entry_id": entry._id, "tag_id": tag_id}
        )
        if not link:
            raise ValueError(f"Tag '{tag_id}' is not attached to this entry")

        await self.statemgr.invalidate(link)

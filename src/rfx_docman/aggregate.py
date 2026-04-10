from asyncpg import UniqueViolationError

from fluvius.domain import Aggregate
from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping, UUID_GENR
from . import helper
from .types import EntryTypeEnum
from .value_objects import CabinetCode, CategoryCode, ShelfCode


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

    async def _ensure_parent_hierarchy(self, *, cabinet_id, parent_path: str):
        """Ensure full folder hierarchy exists for parent_path and return last parent."""
        if not parent_path:
            return None

        parent = None
        current_parent_path = ""

        for segment in parent_path.split("/"):
            current_path = (
                segment if not current_parent_path else f"{current_parent_path}/{segment}"
            )
            existing = await self.statemgr.exist(
                "entry",
                where={"cabinet_id": cabinet_id, "path": current_path},
            )
            if existing:
                if existing.type != EntryTypeEnum.FOLDER:
                    raise ValueError(
                        f"Parent path '{current_path}' exists but is not a folder"
                    )
                parent = existing
                current_parent_path = current_path
                continue

            folder = self.init_resource(
                "entry",
                {
                    "cabinet_id": cabinet_id,
                    "parent_path": current_parent_path,
                    "name": segment,
                    "type": EntryTypeEnum.FOLDER,
                    "media_entry_id": None,
                    "is_virtual": True,
                },
                _id=UUID_GENR(),
            )
            try:
                await self.statemgr.insert(folder)
                await helper.insert_entry_ancestor_rows(
                    self.statemgr,
                    entry_id=folder._id,
                    parent_id=parent._id if parent else None,
                )
                parent = folder
            except UniqueViolationError:
                # Concurrent create of same folder path: re-fetch and continue.
                existing = await self.statemgr.exist(
                    "entry",
                    where={"cabinet_id": cabinet_id, "path": current_path},
                )
                if not existing:
                    raise
                if existing.type != EntryTypeEnum.FOLDER:
                    raise ValueError(
                        f"Parent path '{current_path}' exists but is not a folder"
                    )
                parent = existing

            current_parent_path = current_path

        return parent

    @action("realm-created", resources="realm")
    async def create_realm(self, /, data):
        data = self._serialize(data)
        record = self.init_resource(
            "realm",
            {
                **data,
                "organization_id": str(self.context.organization_id),
            },
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
        category_code = CategoryCode(str(data["code"]))
        shelf_code = ShelfCode(str(shelf.code))

        if not category_code.belongs_to(shelf_code):
            raise ValueError(
                f"Category code {category_code} must belong to shelf {shelf_code}"
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
        cabinet_code = CabinetCode(str(data["code"]))
        category_code = CategoryCode(str(category.code))

        if not cabinet_code.belongs_to(category_code):
            raise ValueError(
                f"Cabinet code {cabinet_code} must belong to category {category_code}"
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
        parent_path = str(data.get("parent_path", ""))
        entry_name = str(data["name"])
        target_path = f"{parent_path}/{entry_name}" if parent_path else entry_name
        is_folder_request = str(data.get("type")) == EntryTypeEnum.FOLDER.value

        try:
            async with self.statemgr.transaction():
                parent = await self._ensure_parent_hierarchy(
                    cabinet_id=cabinet._id,
                    parent_path=str(data.get("parent_path", "")),
                )
                existing = await self.statemgr.exist(
                    "entry",
                    where={"cabinet_id": cabinet._id, "path": target_path},
                )
                if existing:
                    if (
                        is_folder_request
                        and existing.type == EntryTypeEnum.FOLDER
                        and bool(existing.is_virtual)
                    ):
                        await self.statemgr.update(existing, is_virtual=False)
                        return await self.statemgr.fetch("entry", existing._id)
                    raise ValueError(f"An entry already exists at path '{target_path}'")

                record = self.init_resource(
                    "entry",
                    {**data, "cabinet_id": cabinet._id, "is_virtual": False},
                    _id=UUID_GENR(),
                )
                await self.statemgr.insert(record)
                await helper.insert_entry_ancestor_rows(
                    self.statemgr,
                    entry_id=record._id,
                    parent_id=parent._id if parent else None,
                )
                return record
        except UniqueViolationError:
            existing = await self.statemgr.exist(
                "entry",
                where={"cabinet_id": cabinet._id, "path": target_path},
            )
            if (
                existing
                and is_folder_request
                and existing.type == EntryTypeEnum.FOLDER
                and bool(existing.is_virtual)
            ):
                await self.statemgr.update(existing, is_virtual=False)
                return await self.statemgr.fetch("entry", existing._id)
            raise ValueError(f"An entry already exists at path '{target_path}'")

    @action("entry-updated", resources="entry")
    async def update_entry(self, /, data):
        entry = self.rootobj
        updates = self._serialize(data)

        new_path = data.resolve_path(entry)
        old_path = entry.path
        new_parent_path, _ = helper.split_path(new_path)
        old_parent_path = str(entry.parent_path or "")
        parent_changed = new_parent_path != old_parent_path

        if new_path != old_path:
            helper.apply_move_updates(updates, new_path=new_path)

            try:
                async with self.statemgr.transaction():
                    parent = None
                    if parent_changed:
                        parent = await self._ensure_parent_hierarchy(
                            cabinet_id=entry.cabinet_id,
                            parent_path=new_parent_path,
                        )
                    await helper.move_folder_descendants(
                        self.statemgr,
                        entry=entry,
                        old_path=old_path,
                        new_path=new_path,
                    )
                    await self.statemgr.update(entry, **updates)
                    if parent_changed:
                        await helper.rebuild_subtree_ancestors(
                            self.statemgr,
                            entry_id=entry._id,
                            new_parent_id=parent._id if parent else None,
                        )
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

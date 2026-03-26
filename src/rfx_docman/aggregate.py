from fluvius.domain import Aggregate
from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping, UUID_GENR
from .types import EntryTypeEnum
from typing import Any


def _clean_updates(data: dict) -> dict[str, Any]:
    return {k: v for k, v in data.items() if v is not None}


class RFXDocmanAggregate(Aggregate):
    """Docman Aggregate - CRUD operations for document items."""

    @action("realm-created", resources="realm")
    async def create_realm(self, /, data):
        data = serialize_mapping(data)
        record = self.init_resource(
            "realm",
            data,
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        return record

    @action("realm-updated", resources="realm")
    async def update_realm(self, /, data):
        realm = self.rootobj
        updates = _clean_updates(serialize_mapping(data))
        await self.statemgr.update(realm, **updates)
        return await self.statemgr.fetch("realm", realm._id)

    @action("realm-removed", resources="realm")
    async def remove_realm(self, /):
        realm = self.rootobj
        await self.statemgr.invalidate(realm)

    @action("realm-meta-created", resources="realm")
    async def create_realm_meta(self, /, data):
        data = serialize_mapping(data)
        realm = self.rootobj
        record = self.init_resource(
            "realm_meta",
            {
                "realm_id": realm._id,
            },
            data,
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        return record

    @action("realm-meta-updated", resources="realm_meta")
    async def update_realm_meta(self, /, data):
        realm_meta = self.rootobj
        updates = _clean_updates(serialize_mapping(data))
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
        updates = _clean_updates(serialize_mapping(data))

        if "code" in updates:
            code = updates["code"]
            existing = await self.statemgr.exist(
                "shelf",
                where={"realm_id": shelf.realm_id, "code": code},
            )
            if existing and str(existing._id) != str(shelf._id):
                raise ValueError(f"Shelf code {code} already exists in this realm")

        await self.statemgr.update(shelf, **updates)
        return await self.statemgr.fetch("shelf", shelf._id)

    @action("shelf-removed", resources="shelf")
    async def remove_shelf(self, /):
        shelf = self.rootobj

        category_exists = await self.statemgr.exist(
            "category", where={"shelf_id": shelf._id}
        )
        if category_exists:
            raise ValueError("Cannot remove shelf with existing category records")
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

        duplicated = await self.statemgr.exist(
            "category",
            where={"realm_id": shelf.realm_id, "code": code},
        )
        if duplicated:
            raise ValueError(f"Category code {code} already exists in this realm")

        record = self.init_resource(
            "category",
            {
                "realm_id": shelf.realm_id,
                "shelf_id": shelf._id,
                "code": code,
                "name": data["name"],
                "description": data.get("description"),
            },
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        return record

    @action("category-updated", resources="category")
    async def update_category(self, /, data):
        category = self.rootobj
        updates = _clean_updates(serialize_mapping(data))

        if "code" in updates:
            new_code = updates["code"]
            shelf = await self.statemgr.fetch("shelf", category.shelf_id)
            if not new_code.startswith(shelf.code):
                raise ValueError(
                    f"Category code {new_code} must start with shelf code {shelf.code}"
                )

            existing = await self.statemgr.exist(
                "category",
                where={"realm_id": category.realm_id, "code": new_code},
            )
            if existing and str(existing._id) != str(category._id):
                raise ValueError(
                    f"Category code {new_code} already exists in this realm"
                )

        await self.statemgr.update(category, **updates)
        return await self.statemgr.fetch("category", category._id)

    @action("category-removed", resources="category")
    async def remove_category(self, /):
        category = self.rootobj

        cabinet_exists = await self.statemgr.exist(
            "cabinet", where={"category_id": category._id}
        )
        if cabinet_exists:
            raise ValueError("Cannot remove category with existing cabinet records")
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

        duplicated = await self.statemgr.exist(
            "cabinet",
            where={"realm_id": category.realm_id, "code": code},
        )
        if duplicated:
            raise ValueError(f"Cabinet code {code} already exists in this realm")

        record = self.init_resource(
            "cabinet",
            {
                "realm_id": category.realm_id,
                "category_id": category._id,
                "code": code,
                "name": data["name"],
                "description": data.get("description"),
            },
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        return record

    @action("cabinet-updated", resources="cabinet")
    async def update_cabinet(self, /, data):
        cabinet = self.rootobj
        updates = _clean_updates(serialize_mapping(data))

        if "code" in updates:
            new_code = updates["code"]
            category = await self.statemgr.fetch("category", cabinet.category_id)
            prefix = f"{category.code}-"
            if not new_code.startswith(prefix):
                raise ValueError(
                    f"Cabinet code {new_code} must start with category prefix {prefix}"
                )

            existing = await self.statemgr.exist(
                "cabinet",
                where={"realm_id": cabinet.realm_id, "code": new_code},
            )
            if existing and str(existing._id) != str(cabinet._id):
                raise ValueError(
                    f"Cabinet code {new_code} already exists in this realm"
                )

        await self.statemgr.update(cabinet, **updates)
        return await self.statemgr.fetch("cabinet", cabinet._id)

    @action("cabinet-removed", resources="cabinet")
    async def remove_cabinet(self, /):
        cabinet = self.rootobj

        entry_exists = await self.statemgr.exist(
            "entry", where={"cabinet_id": cabinet._id}
        )
        if entry_exists:
            raise ValueError("Cannot remove cabinet with existing entry records")
        await self.statemgr.invalidate(cabinet)

    @action("entry-created", resources="cabinet")
    async def create_entry(self, /, data):

        cabinet = self.rootobj
        full_path = data.computed_path
        exists = await self.statemgr.exist(
            "entry", where={"cabinet_id": cabinet._id, "path": full_path}
        )
        if exists:
            raise ValueError(f"Entry '{full_path}' already exists in this cabinet")
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
            entry_data,
            _id=UUID_GENR(),
        )

        await self.statemgr.insert(record)
        return record

    @action("entry-updated", resources="entry")
    async def update_entry(self, /, data):
        entry = self.rootobj
        updates = _clean_updates(serialize_mapping(data))

        new_path = data.get_computed_path(entry)
        old_path = entry.path

        effective_type = data.type if data.type is not None else entry.type
        if effective_type == EntryTypeEnum.FOLDER:
            updates.pop("size", None)
            updates.pop("mime_type", None)

        if new_path != old_path:
            same_path_entries = await self.statemgr.find_all(
                "entry",
                where={"cabinet_id": entry.cabinet_id, "path": new_path},
            )
            if same_path_entries and any(
                str(item._id) != str(entry._id) for item in same_path_entries
            ):
                raise ValueError(f"Path '{new_path}' already exists in this cabinet")

            updates["path"] = new_path

            if effective_type == EntryTypeEnum.FOLDER:
                descendants = await self.statemgr.find_all(
                    "entry",
                    where={
                        "cabinet_id": entry.cabinet_id,
                        "path:has": f"{old_path}/%",
                    },
                )

                old_prefix = f"{old_path}/"
                new_prefix = f"{new_path}/"
                descendant_ids = {str(item._id) for item in descendants}

                # Pre-compute target paths for all descendants
                target_paths_by_child_id = {}
                target_paths = set()
                for child in descendants:
                    target_child_path = new_prefix + child.path[len(old_prefix):]
                    target_paths_by_child_id[str(child._id)] = target_child_path
                    target_paths.add(target_child_path)

                if target_paths:
                    # Batch check for any existing entries that would conflict
                    existing_under_new_prefix = await self.statemgr.find_all(
                        "entry",
                        where={
                            "cabinet_id": entry.cabinet_id,
                            "path:has": f"{new_prefix}%",
                        },
                    )
                    for item in existing_under_new_prefix:
                        item_id = str(item._id)
                        # Only care about entries whose path matches one of the target paths
                        if (
                            item.path in target_paths
                            and item_id not in descendant_ids
                            and item_id != str(entry._id)
                        ):
                            raise ValueError(
                                f"Path '{item.path}' already exists in this cabinet"
                            )

                for child in descendants:
                    target_child_path = target_paths_by_child_id[str(child._id)]
                    await self.statemgr.update(
                        child,
                        path=target_child_path,
                        name=target_child_path.rsplit("/", 1)[-1],
                    )

        updates.pop("parent_path", None)
        await self.statemgr.update(entry, **updates)
        return await self.statemgr.fetch("entry", entry._id)

    @action("entry-removed", resources="entry")
    async def remove_entry(self, /):
        entry = self.rootobj
        await self.statemgr.invalidate(entry)

    # =========================================================================
    # TAG 
    # =========================================================================

    @action("tag-created", resources="entry")
    async def create_tag(self, /, data):
        """Create a new tag in context of an entry, auto-link via entry_tag."""
        data = serialize_mapping(data)
        entry = self.rootobj

        duplicated = await self.statemgr.exist("tag", where={"name": data["name"]})
        if duplicated:
            raise ValueError(f"Tag '{data['name']}' already exists")

        tag = self.init_resource(
            "tag",
            {
                "name": data["name"],
                "color": data.get("color"),
                "icon": data.get("icon"),
            },
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(tag)

        # Auto-link to the entry that triggered creation
        link = self.init_resource(
            "entry_tag",
            {"entry_id": entry._id, "tag_id": tag._id},
        )
        await self.statemgr.insert(link)
        return tag

    @action("tag-updated", resources="tag")
    async def update_tag(self, /, data):
        """Update name/color/icon of an existing tag."""
        tag = self.rootobj
        updates = _clean_updates(serialize_mapping(data))

        if "name" in updates:
            existing = await self.statemgr.exist("tag", where={"name": updates["name"]})
            if existing and str(existing._id) != str(tag._id):
                raise ValueError(f"Tag '{updates['name']}' already exists")

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

        already_linked = await self.statemgr.exist(
            "entry_tag", where={"entry_id": entry._id, "tag_id": tag_id}
        )
        if already_linked:
            raise ValueError(f"Tag '{tag.name}' is already attached to this entry")

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

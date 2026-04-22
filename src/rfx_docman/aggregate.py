from asyncpg import UniqueViolationError

from fluvius.domain import Aggregate
from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping, UUID_GENR
from . import helper
from .types import EntryTypeEnum
from .value_objects import CabinetCode, CategoryCode, ShelfCode
from fluvius.data.exceptions import DuplicateEntryError, ItemNotFoundError
from fluvius.error import BadRequestError


class RFXDocmanAggregate(Aggregate):
    """Aggregate handlers for docman commands."""

    def _serialize(self, data):
        """Convert payload objects to plain mappings used by state manager."""
        return serialize_mapping(data)

    @action("realm-created", resources="realm")
    async def create_realm(self, /, data):
        """Create a realm under the current organization context."""
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
        """Update mutable realm fields."""
        realm = self.rootobj
        updates = self._serialize(data)
        await self.statemgr.update(realm, **updates)
        return await self.statemgr.fetch("realm", realm._id)

    @action("realm-removed", resources="realm")
    async def remove_realm(self, /):
        """Soft-delete a realm after child-shelf guard checks."""
        realm = self.rootobj
        await self.statemgr.invalidate(realm)

    @action("realm-meta-created", resources="realm")
    async def create_realm_meta(self, /, data):
        """Create a realm-scoped metadata key/value record."""
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
        """Update an existing realm metadata record."""
        realm_meta = self.rootobj
        updates = self._serialize(data)
        await self.statemgr.update(realm_meta, **updates)
        return await self.statemgr.fetch("realm_meta", realm_meta._id)

    @action("realm-meta-removed", resources="realm_meta")
    async def remove_realm_meta(self, /):
        """Soft-delete a realm metadata record."""
        realm_meta = self.rootobj
        await self.statemgr.invalidate(realm_meta)

    @action("shelf-created", resources="realm")
    async def create_shelf(self, /, data):
        """Create a shelf within the selected realm."""
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
        """Update shelf fields."""
        shelf = self.rootobj
        updates = self._serialize(data)
        await self.statemgr.update(shelf, **updates)
        return await self.statemgr.fetch("shelf", shelf._id)

    @action("shelf-removed", resources="shelf")
    async def remove_shelf(self, /):
        """Soft-delete a shelf after child-category guard checks."""
        shelf = self.rootobj
        await self.statemgr.invalidate(shelf)

    @action("category-created", resources="shelf")
    async def create_category(self, /, data):
        """Create a category and validate that its code belongs to the shelf."""
        data = self._serialize(data)
        shelf = self.rootobj
        category_code = CategoryCode(str(data["code"]))
        shelf_code = ShelfCode(str(shelf.code))

        if not category_code.belongs_to(shelf_code):
            raise BadRequestError(
                "D10.002",
                f"Category code {category_code} must belong to shelf {shelf_code}",
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
        """Update category fields."""
        category = self.rootobj
        updates = self._serialize(data)

        await self.statemgr.update(category, **updates)
        return await self.statemgr.fetch("category", category._id)

    @action("category-removed", resources="category")
    async def remove_category(self, /):
        """Soft-delete a category after child-cabinet guard checks."""
        category = self.rootobj
        await self.statemgr.invalidate(category)

    @action("cabinet-created", resources="category")
    async def create_cabinet(self, /, data):
        """Create a cabinet and validate that its code belongs to the category."""
        data = self._serialize(data)
        category = self.rootobj
        cabinet_code = CabinetCode(str(data["code"]))
        category_code = CategoryCode(str(category.code))

        if not cabinet_code.belongs_to(category_code):
            raise BadRequestError(
                "D10.003",
                f"Cabinet code {cabinet_code} must belong to category {category_code}",
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
        """Update cabinet fields."""
        cabinet = self.rootobj
        updates = self._serialize(data)

        await self.statemgr.update(cabinet, **updates)
        return await self.statemgr.fetch("cabinet", cabinet._id)

    @action("cabinet-removed", resources="cabinet")
    async def remove_cabinet(self, /):
        """Soft-delete a cabinet after child-entry guard checks."""
        cabinet = self.rootobj
        await self.statemgr.invalidate(cabinet)

    @action("entry-created", resources="cabinet")
    async def create_entry(self, /, data):
        """Create a file/folder entry in a cabinet with closure-table wiring."""
        cabinet = self.rootobj

        data = self._serialize(data)
        parent_path = str(data.get("parent_path", ""))
        entry_name = str(data["name"])
        target_path = f"{parent_path}/{entry_name}" if parent_path else entry_name
        is_folder_request = str(data.get("type")) == EntryTypeEnum.FOLDER.value

        try:
            # Stage 1: ensure destination parent chain exists.
            parent = await helper.ensure_parent_hierarchy(
                self.statemgr,
                cabinet_id=cabinet._id,
                parent_path=parent_path,
                init_resource=self.init_resource,
                id_generator=UUID_GENR,
            )

            # Stage 2: resolve path conflicts. A virtual folder can be promoted
            # to a real folder request at the same path.
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
                raise DuplicateEntryError(
                    "E00.001",
                    f"An entry already exists at path '{target_path}'",
                )

            # Stage 3: insert entry and closure rows.
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
            # Return via view (_entry) for consistency with update_entry.
            return await self.statemgr.fetch("entry", record._id)
        except UniqueViolationError:
            # Stage 4: concurrent insert race. Re-check path and keep virtual-folder
            # promotion behavior deterministic.
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
            raise DuplicateEntryError(
                "E00.001",
                f"An entry already exists at path '{target_path}'",
            )

    @action("entry-updated", resources="entry")
    async def update_entry(self, /, data):
        """Update entry metadata, rename/move path, and optionally move cabinet."""
        entry = self.rootobj
        updates = self._serialize(data)

        # Stage 1: resolve destination cabinet/path from current state + payload.
        dest_cabinet_id = data.cabinet_id or entry.cabinet_id
        source_cabinet_id = entry.cabinet_id
        cabinet_changed = dest_cabinet_id != source_cabinet_id

        new_path = data.resolve_path(entry)
        old_path = str(entry.path or "")
        new_parent_path, _ = helper.split_path(new_path)
        old_parent_path = str(entry.parent_path or "")
        parent_changed = new_parent_path != old_parent_path or cabinet_changed

        if cabinet_changed:
            updates["cabinet_id"] = dest_cabinet_id

        if new_path != old_path or cabinet_changed:
            # Stage 2: normalize parent_path/name fields from resolved path.
            helper.apply_move_updates(updates, new_path=new_path)

            try:
                parent = None
                if parent_changed:
                    # Stage 3: ensure destination parent chain exists.
                    parent = await helper.ensure_parent_hierarchy(
                        self.statemgr,
                        cabinet_id=dest_cabinet_id,
                        parent_path=new_parent_path,
                        init_resource=self.init_resource,
                        id_generator=UUID_GENR,
                    )

                # Stage 4: move descendant rows (folders only) and update root row.
                await helper.move_folder_descendants(
                    self.statemgr,
                    entry=entry,
                    old_path=old_path,
                    new_path=new_path,
                    source_cabinet_id=source_cabinet_id,
                    dest_cabinet_id=dest_cabinet_id,
                )
                await self.statemgr.update(entry, **updates)
                if parent_changed:
                    # Stage 5: rebuild external ancestor links for moved subtree.
                    await helper.rebuild_subtree_ancestors(
                        self.statemgr,
                        entry_id=entry._id,
                        new_parent_id=parent._id if parent else None,
                    )
            except UniqueViolationError:
                raise DuplicateEntryError(
                    "E00.001",
                    f"An entry already exists at path '{new_path}'",
                )
        else:
            # No move semantics; plain field update.
            await self.statemgr.update(entry, **updates)

        return await self.statemgr.fetch("entry", entry._id)

    @action("entry-removed", resources="entry")
    async def remove_entry(self, /):
        """Soft-delete entry and, for folders, cascade-delete the entire subtree.

        Root entry is invalidated via ``statemgr.invalidate()`` for proper
        ``_etag`` / ``_updater`` bookkeeping. Descendants are bulk soft-deleted
        in a single SQL statement. All closure edges for the subtree are pruned
        atomically within the same transaction.
        """
        entry = self.rootobj
        # Stage 1: soft-delete this entry (handles _etag/_updater bookkeeping).
        await self.statemgr.invalidate(entry)

        if entry.type == EntryTypeEnum.FOLDER:
            # Stage 2A: cascade bulk-delete descendants + prune entire subtree closure.
            await helper.cascade_soft_delete_subtree(
                self.statemgr,
                root_id=entry._id,
            )
        else:
            # Stage 2B: prune closure rows for this single file entry.
            await helper.prune_entry_ancestor_for_soft_delete(
                self.statemgr,
                entry_id=entry._id,
            )

    @action("entry-copied", resources="entry")
    async def copy_entry(self, /, data):
        """Copy an entry subtree to destination cabinet/path with closure rebuild.

        Both `path`/`parent_path` and `entry_ancestor` are updated atomically
        within a single transaction to keep the two sources of truth in sync.
        """
        entry = self.rootobj
        data = self._serialize(data)

        # Stage 1: resolve destination path (pure computation, outside transaction).
        dest_cabinet_id = data["cabinet_id"]
        dest_parent_path = str(data.get("parent_path", "") or "")
        dest_name = str(data.get("name") or entry.name)
        dest_path = f"{dest_parent_path}/{dest_name}" if dest_parent_path else dest_name

        # Wrap stages 2-5 in a single transaction so that path updates
        # and closure inserts are always committed or rolled back together.
        # Stage 2: ensure destination parent hierarchy exists.
        dest_parent = await helper.ensure_parent_hierarchy(
            self.statemgr,
            cabinet_id=dest_cabinet_id,
            parent_path=dest_parent_path,
            init_resource=self.init_resource,
            id_generator=UUID_GENR,
        )

        # Stage 3: destination path must be unique.
        existing = await self.statemgr.exist(
            "entry",
            where={"cabinet_id": dest_cabinet_id, "path": dest_path},
        )
        if existing:
            raise DuplicateEntryError(
                "E00.001",
                f"An entry already exists at destination path '{dest_path}'",
            )

        if entry.type != EntryTypeEnum.FOLDER:
            # Stage 4A: file copy path (single row + closure links).
            new_entry = self.init_resource(
                "entry",
                {
                    "cabinet_id": dest_cabinet_id,
                    "parent_path": dest_parent_path,
                    "name": dest_name,
                    "type": entry.type,
                    "media_entry_id": entry.media_entry_id,
                    "is_virtual": False,
                },
                _id=UUID_GENR(),
            )
            await self.statemgr.insert(new_entry)
            await helper.insert_entry_ancestor_rows(
                self.statemgr,
                entry_id=new_entry._id,
                parent_id=dest_parent._id if dest_parent else None,
            )
            return await self.statemgr.fetch("entry", new_entry._id)

        # Stage 4B: folder copy path (recursive subtree clone).
        # Fetch descendants ordered by depth with a path->old_id index.
        descendants, path_to_old_id = await helper.fetch_entry_subtree(
            self.statemgr, ancestor_id=entry._id
        )

        # Stage 5: clone nodes and re-wire closure relationships.
        id_map: dict = {}
        new_root = None
        src_root_path = str(entry.path)

        for row in descendants:
            old_id = row["_id"]
            old_path = row["_path"]

            if old_id == entry._id:
                # Root of the subtree → maps to dest_path.
                new_parent_path = dest_parent_path
                new_name = dest_name
            else:
                # Remap path relative to the new destination root.
                relative = old_path[len(src_root_path) + 1 :]
                full_new_path = f"{dest_path}/{relative}"
                new_parent_path, new_name = helper.split_path(full_new_path)

            new_id = UUID_GENR()
            id_map[str(old_id)] = new_id

            new_node = self.init_resource(
                "entry",
                {
                    "cabinet_id": dest_cabinet_id,
                    "parent_path": new_parent_path,
                    "name": new_name,
                    "type": row["type"],
                    "media_entry_id": row["media_entry_id"],
                    "is_virtual": bool(row["is_virtual"]),
                },
                _id=new_id,
            )
            await self.statemgr.insert(new_node)

            # Resolve closure parent id with explicit 3-case guard.
            # `path_to_old_id` maps `_path` (== parent_path/name) → _id,
            # so the parent of a row is found at key == row['parent_path'].
            if old_id == entry._id:
                # Root node → wire to destination parent.
                parent_id_for_wiring = dest_parent._id if dest_parent else None
                new_root = new_node
            elif not (old_parent_path := str(row["parent_path"] or "")):
                # Direct child of cabinet root — rare in subtree copy,
                # but guard defensively: wire to subtree root clone.
                parent_id_for_wiring = new_root._id if new_root else None
            elif old_parent_path in path_to_old_id:
                # Normal case: map old parent → new cloned parent.
                old_parent_id = path_to_old_id[old_parent_path]
                parent_id_for_wiring = id_map.get(
                    str(old_parent_id),
                    new_root._id if new_root else None,
                )
            else:
                # Orphaned entry: parent was soft-deleted or outside subtree;
                # fall back to subtree root clone to avoid leaving dangling
                # closure edges.
                parent_id_for_wiring = new_root._id if new_root else None

            await helper.insert_entry_ancestor_rows(
                self.statemgr,
                entry_id=new_id,
                parent_id=parent_id_for_wiring,
            )

        if new_root is None:
            raise RuntimeError(
                "copy_entry: subtree clone produced no root — check entry_ancestor self-link for entry %s"
                % entry._id
            )
        return await self.statemgr.fetch("entry", new_root._id)

    # =========================================================================
    # TAG
    # =========================================================================

    @action("tag-created", resources="tag")
    async def create_tag(self, /, data):
        """Create a globally shared tag."""
        data = self._serialize(data)
        tag = self.init_resource(
            "tag",
            {
                **data,
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
        """Soft-delete a tag."""
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
            raise ItemNotFoundError("E00.006", f"Tag '{tag_id}' does not exist")

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
            raise ItemNotFoundError(
                "E00.006",
                f"Tag '{tag_id}' is not attached to this entry",
            )

        await helper.delete_entry_tag_link(
            self.statemgr,
            entry_id=entry._id,
            tag_id=tag_id,
        )

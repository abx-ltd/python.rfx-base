from fluvius.domain import Aggregate
from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping, UUID_GENR


def _clean_updates(data: dict) -> dict:
    return {k: v for k, v in data.items() if v is not None}


def _normalize_shelf_code(value: str) -> str:
    code = value.strip().upper()
    if len(code) != 1 or not code.isalpha() or not code.isascii():
        raise ValueError("Shelf code must be a single letter A-Z")
    return code


class RFXDocumentAggregate(Aggregate):
    """Document Aggregate - CRUD operations for document items."""

    @action("realm-created", resources="realm")
    async def create_real(self, /, data):
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
        if not updates:
            raise ValueError("At least one field required")
        await self.statemgr.update(realm, **updates)
        return await self.statemgr.fetch("realm", realm._id)

    @action("realm-removed", resources="realm")
    async def remove_realm(self, /):
        realm = self.rootobj
        for child_model in ("realm_meta", "shelf", "category", "cabinet"):
            exists = await self.statemgr.exist(
                child_model, where={"realm_id": realm._id}
            )
            if exists:
                raise ValueError(
                    f"Cannot remove realm with existing {child_model} records"
                )
        await self.statemgr.invalidate(realm)

    @action("shelf-created", resources="realm")
    async def create_shelf(self, /, data):
        data = serialize_mapping(data)
        realm = self.rootobj

        code = data.get("code")
        if not code:
            raise ValueError("Shelf code is required")
        code = _normalize_shelf_code(code)

        duplicated = await self.statemgr.exist(
            "shelf",
            where={"realm_id": realm._id, "code": code},
        )
        if duplicated:
            raise ValueError(f"Shelf code {code} already exists in this realm")

        record = self.init_resource(
            "shelf",
            {
                "realm_id": realm._id,
                "code": code,
                "name": data["name"],
                "description": data.get("description"),
            },
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        return record

    @action("shelf-updated", resources="shelf")
    async def update_shelf(self, /, data):
        shelf = self.rootobj
        data = serialize_mapping(data)

        updates = _clean_updates(data)
        updates.pop("shelf_id", None)
        if not updates:
            raise ValueError("At least one field required")

        if "code" in updates:
            code = _normalize_shelf_code(updates["code"])
            updates["code"] = code
            
            # Check for duplicates in same realm
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

        code = data.get("code")
        if not code:
            raise ValueError("Category code is required")
        
        if not code.startswith(shelf.code):
            raise ValueError(f"Category code {code} must start with shelf code {shelf.code}")

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
        data = serialize_mapping(data)

        updates = _clean_updates(data)
        updates.pop("category_id", None)
        if not updates:
            raise ValueError("At least one field required")

        if "code" in updates:
            new_code = updates["code"]
            # Fetch shelf to check prefix
            shelf = await self.statemgr.fetch("shelf", category.shelf_id)
            if not new_code.startswith(shelf.code):
                raise ValueError(f"Category code {new_code} must start with shelf code {shelf.code}")

            # Duplicate check in realm
            existing = await self.statemgr.exist(
                "category",
                where={"realm_id": category.realm_id, "code": new_code},
            )
            if existing and str(existing._id) != str(category._id):
                raise ValueError(f"Category code {new_code} already exists in this realm")

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

        code = data.get("code")
        if not code:
            raise ValueError("Cabinet code is required")
        
        prefix = f"{category.code}-"
        if not code.startswith(prefix):
            raise ValueError(f"Cabinet code {code} must start with category prefix {prefix}")

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
        data = serialize_mapping(data)

        updates = _clean_updates(data)
        updates.pop("cabinet_id", None)
        if not updates:
            raise ValueError("At least one field required")

        if "code" in updates:
            new_code = updates["code"]
            # Fetch category to check prefix
            category = await self.statemgr.fetch("category", cabinet.category_id)
            prefix = f"{category.code}-"
            if not new_code.startswith(prefix):
                raise ValueError(f"Cabinet code {new_code} must start with category prefix {prefix}")

            # Duplicate check in realm
            existing = await self.statemgr.exist(
                "cabinet",
                where={"realm_id": cabinet.realm_id, "code": new_code},
            )
            if existing and str(existing._id) != str(cabinet._id):
                raise ValueError(f"Cabinet code {new_code} already exists in this realm")

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

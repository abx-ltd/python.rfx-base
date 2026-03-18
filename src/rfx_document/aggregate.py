import string

from fluvius.domain import Aggregate
from fluvius.domain.aggregate import action
from fluvius.data import serialize_mapping, UUID_GENR
from fluvius.domain.aggregate import Aggregate, action


def _clean_updates(data: dict) -> dict:
    return {k: v for k, v in data.items() if v is not None}


def _normalize_shelf_code(value: str) -> str:
    code = value.strip().upper()
    if len(code) != 1 or not code.isalpha() or not code.isascii():
        raise ValueError("Shelf code must be a single letter A-Z")
    return code

class RFXDocumentAggregate(Aggregate):
    """Document Aggregate - CRUD operations for document items."""

    @action("real-created", resources='realm')
    async def create_real(self, /, data):
        data = serialize_mapping(data)
        record = self.init_resource(
            "realm",
            data,
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        return record

    @action("realm-updated", resources='realm')
    async def update_realm(self, /, data):
        realm = self.rootobj
        updates = _clean_updates(serialize_mapping(data))
        if not updates:
            raise ValueError("At least one field required")
        await self.statemgr.update(realm, **updates)
        return await self.statemgr.fetch("realm", realm._id)

    @action("realm-removed", resources='realm')
    async def remove_realm(self, /):
        realm = self.rootobj
        for child_model in ("realm_meta", "shelf", "category", "cabinet"):
            exists = await self.statemgr.exist(child_model, where={"realm_id": realm._id})
            if exists:
                raise ValueError(f"Cannot remove realm with existing {child_model} records")
        await self.statemgr.invalidate(realm)

    async def _next_shelf_code(self, realm_id: str) -> str:
        shelves = await self.statemgr.find_all("shelf", where={"realm_id": realm_id})
        used_codes = {
            str(shelf.code).upper()
            for shelf in shelves
            if getattr(shelf, "code", None)
        }
        for code in string.ascii_uppercase:
            if code not in used_codes:
                return code
        raise ValueError("No available shelf code in range A-Z")

    @action("shelf-created", resources='shelf')
    async def create_shelf(self, /, data):
        data = serialize_mapping(data)
        realm_id = data["realm_id"]
        realm = await self.statemgr.find_one("realm", where={"_id": realm_id})
        if not realm:
            raise ValueError(f"realm {realm_id} is not existed")

        code = data.get("code")
        if code is None:
            code = await self._next_shelf_code(realm_id)
        code = _normalize_shelf_code(code)

        duplicated = await self.statemgr.exist(
            "shelf",
            where={"realm_id": realm_id, "code": code},
        )
        if duplicated:
            raise ValueError(f"Shelf code {code} already exists in this realm")

        record = self.init_resource(
            "shelf",
            {
                "realm_id": realm_id,
                "code": code,
                "name": data["name"],
                "description": data.get("description"),
            },
            _id=UUID_GENR(),
        )
        await self.statemgr.insert(record)
        return record

    @action("shelf-updated", resources='shelf')
    async def update_shelf(self, /, data):
        shelf = self.rootobj
        updates = _clean_updates(serialize_mapping(data))
        if not updates:
            raise ValueError("At least one field required")

        if "code" in updates:
            updates["code"] = _normalize_shelf_code(updates["code"])
            existing = await self.statemgr.exist(
                "shelf",
                where={"realm_id": shelf.realm_id, "code": updates["code"]},
            )
            if existing and str(existing._id) != str(shelf._id):
                raise ValueError(f"Shelf code {updates['code']} already exists in this realm")

        await self.statemgr.update(shelf, **updates)
        return await self.statemgr.fetch("shelf", shelf._id)

    @action("shelf-removed", resources='shelf')
    async def remove_shelf(self, /):
        shelf = self.rootobj
        category_exists = await self.statemgr.exist("category", where={"shelf_id": shelf._id})
        if category_exists:
            raise ValueError("Cannot remove shelf with existing category records")
        await self.statemgr.invalidate(shelf)
"""
Utility script to populate a system organization.
"""

import argparse
import asyncio
from fluvius.data import UUID_GENR
from datetime import UTC, datetime
from uuid import UUID

from rfx_base import config
from rfx_user.state import IDMStateManager


async def populate_sys_org(org_name: str):
    manager = IDMStateManager(None)

    data = {
        "_id": str(UUID_GENR()),
        "_created": datetime(2026, 3, 17, 14, 11, 24, 87000, tzinfo=UTC),
        "_creator": UUID("2fb8949a-0c1d-42b3-9515-b90a2633b68e"),
        "_updated": datetime(2026, 3, 17, 14, 11, 24, 163000, tzinfo=UTC),
        "_etag": "qh2Dne0nfUbvNldFB5CAAsOKKGlx5MYr5rz3jlwXHmM",
        "description": "SYSTEM ORGANIZATION",
        "name": org_name,
        "system_entity": True,
        "active": True,
        "system_tag": [],
        "user_tag": [],
        "organization_code": None,
        "status": "ACTIVE",
        "business_name": "SYSTEM ORGANIZATION",
    }

    # Use a transaction for database operations
    async with manager.transaction():
        # Check if the organization already exists
        exists = await manager.exist("organization", where=dict(_id=data["_id"]))
        if exists:
            print(f"System organization already exists: {exists.name}")
            return

        # Use the state manager to create and insert
        record = manager.create("organization", **data)
        await manager.insert(record)

    print(f"Successfully populated organization: {org_name}")


def main():
    parser = argparse.ArgumentParser(description="Populate a default system organization.")
    parser.add_argument("name", type=str, help="Name of the organization")
    args = parser.parse_args()

    asyncio.run(populate_sys_org(args.name))


if __name__ == "__main__":
    main()

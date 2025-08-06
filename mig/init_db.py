from fluvius.domain.logstore.sql import SQLDomainLogManager, DomainLogBaseModel
from fluvius.tracker.model import SQLTrackerDataModel
from fluvius.media.model import MediaSchema

async def init_db():
    manager = SQLDomainLogManager(None)
    db = manager.connector._async_session._async_engine
    async with db.begin() as conn:
        await conn.run_sync(DomainLogBaseModel.metadata.drop_all)
        await conn.run_sync(DomainLogBaseModel.metadata.create_all)

        await conn.run_sync(SQLTrackerDataModel.metadata.drop_all)
        await conn.run_sync(SQLTrackerDataModel.metadata.create_all)

        await conn.run_sync(MediaSchema.metadata.drop_all)
        await conn.run_sync(MediaSchema.metadata.create_all)

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())

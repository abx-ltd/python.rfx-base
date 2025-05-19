""" Complex forms management domain (e.g. contract management)
    Allow generating form elements with just pydantic schema
"""

from fluvius.data import DataModel, Field, UUID_TYPE


class DataElement(DataModel):
    group_id: UUID_TYPE = Field(alias='_created')
    package_id: UUID_TYPE = Field(alias='_created')
    schema_name: UUID_TYPE = Field(alias='_created')
    schema_revision: int = 0

    id_: UUID_TYPE = Field(alias='_id')
    created_: str = Field(alias='_created')
    updated_: str = Field(alias='_updated')
    creator_: str = Field(alias='_creator')
    updater_: str = Field(alias='_updater')



class DataGroup(DataModel):
    pass


class DataPackage(DataModel):
    pass

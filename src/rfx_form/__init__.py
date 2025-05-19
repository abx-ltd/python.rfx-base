""" Complex forms management domain (e.g. contract management)
    Allow generating form elements with just pydantic schema
"""

from fluvius.data import DataModel, Field, UUID_TYPE


class DataElement(DataModel):
    form_id: UUID_TYPE
    package_id: UUID_TYPE

    schema_name: str = Field(alias='_schema')
    revision_number: int = Field(alias='_revision')
    element_id: UUID_TYPE = Field(alias='_id')
    created_time: str = Field(alias='_created')
    updated_time: str = Field(alias='_updated')
    creator_profile: str = Field(alias='_creator')
    updater_profile: str = Field(alias='_updater')



class DataForm(DataModel):
    pass


class DataPackage(DataModel):
    pass

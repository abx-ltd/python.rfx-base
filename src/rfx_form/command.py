from fluvius.data import serialize_mapping, DataModel
from .domain import FormManagementDomain
from . import logger

processor = FormManagementDomain.command_processor
Command = FormManagementDomain.Command


class SubmitForm(Command):
    """Submit and lock the form"""

    class Meta(Command.Meta):
        key = "submit-form"
        name = "Submit Form"
        resource_init = True
        resource_desc = "Resource key. e.g. `user`"

    class Data(DataModel):
        name__given: str
        name__family: str

    @processor
    async def process(self, aggregate, statemgr, payload):
        data = serialize_mapping(payload)
        logger.info("Workon data: %r" % data)

        yield None
        # aggroot = aggregate.get_aggroot()
        # user = statemgr.create('user', data, _id=aggroot.identifier)
        # logger.info('/3rd/ Non-annotated processor (default) called: %s', aggroot)
        # yield aggregate.create_response(serialize_mapping(user), _type="user-response")


class UnsubmitForm(Command):
    """Unlock the form"""

    class Meta(Command.Meta):
        key = "unsubmit-form"
        name = "Unsubmit Form"
        resource_init = True
        resource_desc = "Resource key. e.g. `user`"


class SaveForm(Command):
    """Submit and lock the form"""

    class Meta(Command.Meta):
        key = "save-form"
        name = "Save Form"
        resource_init = True
        resource_desc = "Resource key. e.g. `user`"


class DeleteForm(Command):
    """Submit and lock the form"""

    class Meta(Command.Meta):
        key = "delete-form"


class SaveElement(Command):
    """Submit and lock the form"""

    class Meta(Command.Meta):
        key = "save-element"
        name = "Save Element"
        resource_init = True
        resource_desc = "Resource key. e.g. `user`"


class DeleteElemenet(Command):
    """Submit and lock the form"""

    class Meta(Command.Meta):
        key = "delete-form"


class CreatePackage(Command):
    """Submit and lock the form"""

    class Meta(Command.Meta):
        key = "save-element"
        name = "Save Element"
        resource_init = True
        resource_desc = "Resource key. e.g. `user`"

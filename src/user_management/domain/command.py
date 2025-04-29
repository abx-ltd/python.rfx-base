from fluvius.data import serialize_mapping, DataModel

from user_management import logger

from .domain import _processor, UserManagementDomain


Command = UserManagementDomain.Command


class UserModel(DataModel):
	name__given: str
	name__family: str


class CreateUserCmd(Command):
	class Meta:
		key = 'create-user'
		name = 'Create User'
		new_resource = True
		resource_desc = 'Resource key. e.g. `user`'

	Data = UserModel

	@_processor
	async def _process(self, aggregate, statemgr, payload):
		data = serialize_mapping(payload)
		logger.info("Workon data: %r" % data)

		yield None
		# aggroot = aggregate.get_aggroot()
		# user = statemgr.create('user', data, _id=aggroot.identifier)
		# logger.info('/3rd/ Non-annotated processor (default) called: %s', aggroot)
		# yield aggregate.create_response(serialize_mapping(user), _type="user-response")

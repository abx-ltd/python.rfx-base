from fluvius.data import serialize_mapping, DataModel
from .domain import IDMDomain
from . import logger

processor = IDMDomain.command_processor


class CreateUserCmd(IDMDomain.Command):
	""" Create a new user account """

	class Meta:
		key = 'create-user'
		name = 'Create User'
		new_resource = True
		resource_docs = 'Resource key. e.g. `user`'

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

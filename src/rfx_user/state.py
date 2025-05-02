from fluvius.domain.state import DataAccessManager
from .model import UserManagementConnector

class UserManagementStateManager(DataAccessManager):
    __connector__ = UserManagementConnector
    __auto_model__ = 'schema'

from fluvius.casbin import PolicyManager, PolicySchema
from rfx_schema.rfx_user._viewmap import PolicyIDMProfileView
from . import config
from .model import IDMConnector

class IDMPolicyManager(PolicyManager):
	__schema__ = PolicyIDMProfileView

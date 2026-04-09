from fluvius.casbin import PolicyManager, PolicySchema
from rfx_schema.rfx_docman import RFXDocmanConnector
from rfx_schema.rfx_docman._viewmap import PolicyDocmanView
from . import config


# class RFXDocmanPolicy(RFXDocmanConnector.__data_schema_base__, PolicySchema):
#     __table_args__ = dict(schema=config.RFX_POLICY_SCHEMA)
#     __tablename__ = config.POLICY_TABLE


class RFXDocmanPolicyManager(PolicyManager):
    __schema__ = PolicyDocmanView

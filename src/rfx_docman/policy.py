from fluvius.casbin import PolicyManager
from rfx_schema.rfx_docman._viewmap import PolicyDocmanView

class RFXDocmanPolicyManager(PolicyManager):
    __schema__ = PolicyDocmanView

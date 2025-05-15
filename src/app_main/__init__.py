from rfx_idm import IDMDomain, IDMQueryManager
from rfx_user import UserProfileDomain, UserProfileQueryManager

from . import setup

app = setup.bootstrap()
app = setup.configure_domain_manager(app, IDMDomain, UserProfileDomain)
app = setup.configure_query_manager(app, IDMQueryManager, UserProfileQueryManager)

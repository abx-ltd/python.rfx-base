from rfx_idm import IDMDomain, IDMQueryManager

from . import setup

app = setup.bootstrap()
app = setup.configure_domain_manager(app, IDMDomain)
app = setup.configure_query_manager(app, IDMQueryManager)

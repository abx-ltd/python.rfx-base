from fluvius.fastapi import (
    create_app,
    configure_authentication,
    configure_domain_manager,
    configure_query_manager)

domains = (
    'rfx_idm.IDMDomain',
    'rfx_user.UserProfileDomain',
)

queries = (
    'rfx_idm.IDMQueryManager',
    'rfx_user.UserProfileQueryManager',
)

app = create_app() \
    | configure_authentication() \
    | configure_domain_manager(*domains) \
    | configure_query_manager(*queries)

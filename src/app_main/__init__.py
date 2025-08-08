from fluvius.fastapi import (
    create_app,
    configure_authentication,
    configure_domain_manager,
    configure_query_manager,
    # configure_mqtt,
)

from rfx_idm import IDMDomain

domains = (
    IDMDomain,
    'rfx_user.UserProfileDomain',
    'rfx_message.MessageServiceDomain',
)

queries = (
    'rfx_idm.IDMQueryManager',
    'rfx_user.UserProfileQueryManager',
    'rfx_message.MessageQueryManager',
)

app = create_app() \
    | configure_authentication() \
    | configure_domain_manager(*domains) \
    | configure_query_manager(*queries) \
    # | configure_mqtt()

from fluvius.fastapi import KCAdmin, config

kc_admin = KCAdmin(
    app=None,
    server_url=config.KEYCLOAK_BASE_URL,
    client_id=config.KEYCLOAK_CLIENT_ID,
    client_secret=config.KEYCLOAK_CLIENT_SECRET,
    realm_name=config.KEYCLOAK_REALM
)

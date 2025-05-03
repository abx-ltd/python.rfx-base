from fluvius.fastapi import create_app, setup_authentication
from fluvius.fastapi.domain import configure_domain_manager, configure_query_manager

def bootstrap():
    app = create_app()
    app = setup_authentication(app)
    return app

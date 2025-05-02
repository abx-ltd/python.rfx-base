from fluvius.fastapi import create_app, setup_authentication
from fluvius.fastapi.domain import configure_domain_manager, configure_query_manager

def bootstrap(*domains):
    app = create_app()
    app = setup_authentication(app)
    app = configure_domain_manager(app, *domains)
    return app

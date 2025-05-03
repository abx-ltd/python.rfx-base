from fluvius.fastapi import (
    create_app,
    setup_authentication,
    configure_domain_manager,
    configure_query_manager)

def bootstrap():
    app = create_app()
    app = setup_authentication(app)
    return app

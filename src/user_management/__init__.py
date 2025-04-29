from fluvius.fastapi import create_app, setup_authentication
from fluvius.fastapi.domain import configure_domain_manager

from ._meta import config, logger


def __bootstrap__(app=None):
	from user_management.domain import UserManagementDomain
	
	if not app:
		app = create_app()
	
	app = setup_authentication(app)
	app = configure_domain_manager(app, UserManagementDomain)

	return app

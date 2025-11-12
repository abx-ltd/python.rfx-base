import os
from rfx_schema import logger
from rfx_base import config

from alembic_utils.pg_view import PGView
from alembic_utils.replaceable_entity import register_entities


user_profile_view = PGView(
    schema=config.RFX_USER_SCHEMA,
    signature="_profile",
    definition=f"""
    SELECT profile._created,
    profile._creator,
    profile._deleted,
    profile._etag,
    profile._id,
    profile._updated,
    profile._updater,
    profile.access_tags,
    profile.active,
    profile.address__city,
    profile.address__country,
    profile.address__line1,
    profile.address__line2,
    profile.address__postal,
    profile.address__state,
    profile.picture_id,
    profile.birthdate,
    profile.expiration_date,
    profile.gender,
    profile.language,
    profile.last_login,
    profile.name__family,
    profile.name__given,
    profile.name__middle,
    profile.name__prefix,
    profile.name__suffix,
    profile.realm,
    profile.svc_access,
    profile.svc_secret,
    profile.user_tag,
    profile.telecom__email,
    profile.telecom__fax,
    profile.telecom__phone,
    profile.tfa_method,
    profile.tfa_token,
    profile.two_factor_authentication,
    profile.upstream_user_id,
    profile.user_type,
    profile.username,
    profile.verified_email,
    profile.verified_phone,
    profile.primary_language,
    profile.npi,
    profile.verified_npi,
    profile.last_sync,
    profile.is_super_admin,
    profile.system_tag,
    profile.user_id,
    profile.current_profile,
    profile.organization_id,
    profile.preferred_name,
    profile.default_theme,
    profile._realm,
    profile.status
    FROM "{config.RFX_USER_SCHEMA}".profile;
    """
)


def register_pg_entities(allow):
    if not allow:
        logger.info('REGISTER_PG_ENTITIES is not set.')
        return
    register_entities([
        user_profile_view,
    ])

register_pg_entities(os.environ.get('REGISTER_PG_ENTITIES'))

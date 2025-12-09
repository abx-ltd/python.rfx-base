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

user_profile_list_view = PGView(
    schema=config.RFX_USER_SCHEMA,
    signature="_profile_list",
    definition=f"""
    SELECT
        profile._created,
        profile._creator,
        profile._deleted,
        profile._etag,
        profile._id,
        profile._updated,
        profile._updater,
        profile._realm,
        profile.name__family,
        profile.name__given,
        profile.preferred_name,
        profile.username,
        profile.status,
        profile.active,
        profile.organization_id,
        profile.user_id,
        organization.name AS organization_name,
        COALESCE(role_list.role_keys, '{{}}'::character varying[]) AS role_keys
    FROM "{config.RFX_USER_SCHEMA}".profile AS profile
    LEFT JOIN "{config.RFX_USER_SCHEMA}".organization AS organization
        ON profile.organization_id = organization._id
    LEFT JOIN LATERAL (
        SELECT
            array_agg(DISTINCT profile_role.role_key)
                FILTER (WHERE profile_role.role_key IS NOT NULL) AS role_keys
        FROM "{config.RFX_USER_SCHEMA}".profile_role AS profile_role
        WHERE profile_role.profile_id = profile._id
    ) AS role_list ON true;
    """
)

org_member_view = PGView(
    schema=config.RFX_USER_SCHEMA,
    signature="_org_member",
    definition=f"""
    SELECT
        profile._created,
        profile._creator,
        profile._deleted,
        profile._etag,
        profile._id,
        profile._updated,
        profile._updater,
        profile._realm,
        profile.user_id,
        profile.organization_id,
        organization.name AS organization_name,
        profile.name__given,
        profile.name__middle,
        profile.name__family,
        profile.telecom__email,
        profile.telecom__phone,
        profile.status AS profile_status,
        profile_role.role_key AS profile_role,
        COALESCE(policy_counts.policy_count, 0) AS policy_count
    FROM "{config.RFX_USER_SCHEMA}".profile AS profile
    JOIN "{config.RFX_USER_SCHEMA}".organization AS organization
        ON profile.organization_id = organization._id
    JOIN "{config.RFX_USER_SCHEMA}".profile_role AS profile_role
        ON profile._id = profile_role.profile_id
    LEFT JOIN LATERAL (
        SELECT COUNT(*) AS policy_count
        FROM "{config.RFX_POLICY_SCHEMA}"._policy__user_profile AS policy
        WHERE policy.org = organization._id::character varying(255)
            AND policy._deleted IS NULL
    ) AS policy_counts ON true;
    """
)

def register_pg_entities(allow):
    allow_flag = str(allow).lower() in ("1", "true", "yes", "on")
    if not allow_flag:
        logger.info('REGISTER_PG_ENTITIES is disabled or not set.')
        return
    register_entities([
        user_profile_view,
        user_profile_list_view,
        org_member_view,
    ])

register_pg_entities(os.environ.get('REGISTER_PG_ENTITIES'))

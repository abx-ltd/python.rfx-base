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
        profile.realm,
        profile.status,
        profile.active,
        profile.organization_id,
        profile.telecom__email,
        profile.telecom__phone,
        profile.user_id,
        profile.current_profile,
        organization.name AS organization_name,
        COALESCE(profile_role.role_keys, ARRAY[]::varchar[]) AS profile_roles
    FROM "{config.RFX_USER_SCHEMA}".profile AS profile
    LEFT JOIN "{config.RFX_USER_SCHEMA}".organization AS organization
        ON profile.organization_id = organization._id
    LEFT JOIN (
        SELECT profile_id, array_agg(role_key) AS role_keys
        FROM "{config.RFX_USER_SCHEMA}".profile_role
        WHERE _deleted IS NULL
        GROUP BY profile_id
    ) AS profile_role
        ON profile._id = profile_role.profile_id;
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
        profile.realm,
        profile.status AS profile_status,
        COALESCE(profile_role.role_keys, ARRAY[]::varchar[]) AS profile_roles,
        COALESCE(policy_counts.policy_count, 0) AS policy_count
    FROM "{config.RFX_USER_SCHEMA}".profile AS profile
    JOIN "{config.RFX_USER_SCHEMA}".organization AS organization
        ON profile.organization_id = organization._id
    LEFT JOIN (
        SELECT profile_id, array_agg(role_key) AS role_keys
        FROM "{config.RFX_USER_SCHEMA}".profile_role
        WHERE _deleted IS NULL
        GROUP BY profile_id
    ) AS profile_role
        ON profile._id = profile_role.profile_id
    LEFT JOIN LATERAL (
        SELECT COUNT(*) AS policy_count
        FROM "{config.RFX_POLICY_SCHEMA}"._policy__user_profile AS policy
        WHERE policy.org = organization._id::character varying(255)
            AND policy._deleted IS NULL
    ) AS policy_counts ON true;
    """
)

policy_user_profile_view = PGView(
    schema=config.RFX_POLICY_SCHEMA,
    signature="_policy__user_profile",
    definition=f"""
SELECT uuid_generate_v4() AS _id,
    'p'::character varying(255) AS ptype,
    pol_rol.role_key AS role,
    NULL::character varying(255) AS usr,
    NULL::character varying(255) AS pro,
    NULL::character varying(255) AS org,
    NULL::character varying(255) AS rid,
    pol_rol.scope::character varying(255) AS scope,
    pol_res.action::character varying(255) AS act,
    pol_res.cqrs::character varying(255) AS cqrs,
    pol_res.meta::text AS meta,
    NULL::timestamp without time zone AS _deleted
   FROM {config.RFX_POLICY_SCHEMA}.policy_role pol_rol
     JOIN {config.RFX_POLICY_SCHEMA}.policy_resource pol_res ON pol_rol.policy_key::text = pol_res.policy_key::text
  WHERE pol_res.domain::text = ANY (ARRAY['user-profile'::text, '*'::text])
UNION ALL
 SELECT uuid_generate_v4() AS _id,
    'g'::character varying(255) AS ptype,
    NULL::character varying(255) AS role,
    profile.user_id::character varying(255) AS usr,
    profile._id::character varying(255) AS pro,
    profile.organization_id::character varying(255) AS org,
    NULL::character varying(255) AS rid,
    NULL::character varying(255) AS scope,
    NULL::character varying(255) AS act,
    NULL::character varying(255) AS cqrs,
    NULL::text AS meta,
    NULL::timestamp without time zone AS _deleted
   FROM {config.RFX_USER_SCHEMA}.profile
  WHERE profile._deleted IS NULL AND profile.user_id IS NOT NULL AND profile.organization_id IS NOT NULL
UNION ALL
 SELECT uuid_generate_v4() AS _id,
    'g2'::character varying(255) AS ptype,
    pro_rol.role_key AS role,
    NULL::character varying(255) AS usr,
    profile._id::character varying(255) AS pro,
    NULL::character varying(255) AS org,
    NULL::character varying(255) AS rid,
    NULL::character varying(255) AS scope,
    NULL::character varying(255) AS act,
    NULL::character varying(255) AS cqrs,
    NULL::text AS meta,
    NULL::timestamp without time zone AS _deleted
   FROM {config.RFX_USER_SCHEMA}.profile_role pro_rol
     JOIN {config.RFX_USER_SCHEMA}.profile profile ON profile._id = pro_rol.profile_id
  WHERE pro_rol._deleted IS NULL
    AND profile._deleted IS NULL
    AND profile.organization_id IS NOT NULL
UNION ALL
 SELECT uuid_generate_v4() AS _id,
    'g3'::character varying(255) AS ptype,
    'self-access'::character varying(255) AS role,
    NULL::character varying(255) AS usr,
    profile._id::character varying(255) AS pro,
    NULL::character varying(255) AS org,
    profile._id::character varying(255) AS rid,
    NULL::character varying(255) AS scope,
    NULL::character varying(255) AS act,
    NULL::character varying(255) AS cqrs,
    NULL::text AS meta,
    NULL::timestamp without time zone AS _deleted
   FROM {config.RFX_USER_SCHEMA}.profile
  WHERE profile._deleted IS NULL
    AND profile.user_id IS NOT NULL;
    """
)

policy_idm_profile_view = PGView(
    schema=config.RFX_POLICY_SCHEMA,
    signature="_policy__idm_profile",
    definition=f"""
SELECT uuid_generate_v4() AS _id,
    'p'::character varying(255) AS ptype,
    pol_rol.role_key AS role,
    NULL::character varying(255) AS usr,
    NULL::character varying(255) AS pro,
    NULL::character varying(255) AS org,
    NULL::character varying(255) AS rid,
    pol_rol.scope::character varying(255) AS scope,
    pol_res.action::character varying(255) AS act,
    pol_res.cqrs::character varying(255) AS cqrs,
    pol_res.meta::text AS meta,
    NULL::timestamp without time zone AS _deleted
   FROM {config.RFX_POLICY_SCHEMA}.policy_role pol_rol
     JOIN {config.RFX_POLICY_SCHEMA}.policy_resource pol_res ON pol_rol.policy_key::text = pol_res.policy_key::text
  WHERE pol_res.domain::text = ANY (ARRAY['idm-service'::text, '*'::text])
UNION ALL
 SELECT uuid_generate_v4() AS _id,
    'g'::character varying(255) AS ptype,
    NULL::character varying(255) AS role,
    profile.user_id::character varying(255) AS usr,
    profile._id::character varying(255) AS pro,
    profile.organization_id::character varying(255) AS org,
    NULL::character varying(255) AS rid,
    NULL::character varying(255) AS scope,
    NULL::character varying(255) AS act,
    NULL::character varying(255) AS cqrs,
    NULL::character varying(255) AS meta,
    NULL::timestamp without time zone AS _deleted
   FROM {config.RFX_USER_SCHEMA}.profile
  WHERE profile._deleted IS NULL AND profile.user_id IS NOT NULL AND profile.organization_id IS NOT NULL
UNION ALL
 SELECT uuid_generate_v4() AS _id,
    'g2'::character varying(255) AS ptype,
    pro_rol.role_key AS role,
    NULL::character varying(255) AS usr,
    profile._id::character varying(255) AS pro,
    NULL::character varying(255) AS org,
    NULL::character varying(255) AS rid,
    NULL::character varying(255) AS scope,
    NULL::character varying(255) AS act,
    NULL::character varying(255) AS cqrs,
    NULL::character varying(255) AS meta,
    NULL::timestamp without time zone AS _deleted
   FROM {config.RFX_USER_SCHEMA}.profile_role pro_rol
     JOIN {config.RFX_USER_SCHEMA}.profile profile ON profile._id = pro_rol.profile_id
  WHERE pro_rol._deleted IS NULL
    AND profile._deleted IS NULL
    AND profile.organization_id IS NOT NULL
UNION ALL
 SELECT uuid_generate_v4() AS _id,
    'g3'::character varying(255) AS ptype,
    'self-access'::character varying(255) AS role,
    NULL::character varying(255) AS usr,
    profile._id::character varying(255) AS pro,
    NULL::character varying(255) AS org,
    profile._id::character varying(255) AS rid,
    NULL::character varying(255) AS scope,
    NULL::character varying(255) AS act,
    NULL::character varying(255) AS cqrs,
    NULL::character varying(255) AS meta,
    NULL::timestamp without time zone AS _deleted
   FROM {config.RFX_USER_SCHEMA}.profile
  WHERE profile._deleted IS NULL
    AND profile.user_id IS NOT NULL;
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
        policy_user_profile_view,
        policy_idm_profile_view,
    ])

register_pg_entities(os.environ.get('REGISTER_PG_ENTITIES'))

from . import SCHEMA

from rfx_base import config
from alembic_utils.pg_view import PGView
from alembic_utils.replaceable_entity import register_entities
import os

# policy_user_profile_view = PGView(
#     schema=schema_config.RFX_POLICY_SCHEMA,
#     signature="_policy__user_profile",
#     definition=f"""
# SELECT uuid_generate_v4() AS _id,
#     'p'::character varying(255) AS ptype,
#     pol_rol.role_key AS role,
#     NULL::character varying(255) AS sub,
#     NULL::character varying(255) AS org,
#     pol_res.domain AS dom,
#     pol_res.resource AS res,
#     NULL::character varying(255) AS rid,
#     pol_res.action AS act,
#     pol_res.cqrs::character varying(255) AS cqrs,
#     concat_ws(''::text, pol_res.meta)::character varying(255) AS meta,
#     NULL::timestamp without time zone AS _deleted
#    FROM {schema_config.RFX_POLICY_SCHEMA}.policy_role pol_rol
#      JOIN {schema_config.RFX_POLICY_SCHEMA}.policy_resource pol_res ON pol_rol.policy_key::text = pol_res.policy_key::text
#   WHERE pol_res.domain::text = ANY (ARRAY['user-profile'::text, '*'::text])
# UNION ALL
#  SELECT uuid_generate_v4() AS _id,
#     'g'::character varying(255) AS ptype,
#     pro_rol.role_key AS role,
#     profile._id::character varying(255) AS sub,
#     profile.organization_id::character varying(255) AS org,
#     NULL::character varying(255) AS dom,
#     NULL::character varying(255) AS res,
#     NULL::character varying(255) AS rid,
#     NULL::character varying(255) AS act,
#     NULL::character varying(255) AS cqrs,
#     NULL::character varying(255) AS meta,
#     NULL::timestamp without time zone AS _deleted
#    FROM {schema_config.RFX_USER_SCHEMA}.profile
#      JOIN {schema_config.RFX_USER_SCHEMA}.profile_role pro_rol ON profile._id = pro_rol.profile_id
#   WHERE pro_rol._deleted IS NULL
# UNION ALL
#  SELECT uuid_generate_v4() AS _id,
#     'g2'::character varying(255) AS ptype,
#     NULL::character varying(255) AS role,
#     NULL::character varying(255) AS sub,
#     organization._id::character varying(255) AS org,
#     'user-profile'::character varying(255) AS dom,
#     'organization'::character varying(255) AS res,
#     organization._id::character varying(255) AS rid,
#     NULL::character varying(255) AS act,
#     NULL::character varying(255) AS cqrs,
#     NULL::character varying(255) AS meta,
#     NULL::timestamp without time zone AS _deleted
#    FROM {schema_config.RFX_USER_SCHEMA}.organization
# UNION ALL
#  SELECT uuid_generate_v4() AS _id,
#     'g2'::character varying(255) AS ptype,
#     NULL::character varying(255) AS role,
#     NULL::character varying(255) AS sub,
#     invitation.organization_id::character varying(255) AS org,
#     'user-profile'::character varying(255) AS dom,
#     'invitation'::character varying(255) AS res,
#     invitation._id::character varying(255) AS rid,
#     NULL::character varying(255) AS act,
#     NULL::character varying(255) AS cqrs,
#     NULL::character varying(255) AS meta,
#     NULL::timestamp without time zone AS _deleted
#    FROM {schema_config.RFX_USER_SCHEMA}.invitation
#   WHERE invitation.organization_id IS NOT NULL
# UNION ALL
#  SELECT uuid_generate_v4() AS _id,
#     'g2'::character varying(255) AS ptype,
#     NULL::character varying(255) AS role,
#     NULL::character varying(255) AS sub,
#     profile.organization_id::character varying(255) AS org,
#     'user-profile'::character varying(255) AS dom,
#     'profile'::character varying(255) AS res,
#     profile._id::character varying(255) AS rid,
#     NULL::character varying(255) AS act,
#     NULL::character varying(255) AS cqrs,
#     NULL::character varying(255) AS meta,
#     NULL::timestamp without time zone AS _deleted
#    FROM {schema_config.RFX_USER_SCHEMA}.profile
#   WHERE profile.organization_id IS NOT NULL
# UNION ALL
#  SELECT uuid_generate_v4() AS _id,
#     'g2'::character varying(255) AS ptype,
#     NULL::character varying(255) AS role,
#     NULL::character varying(255) AS sub,
#     profile.organization_id::character varying(255) AS org,
#     'user-profile'::character varying(255) AS dom,
#     'user'::character varying(255) AS res,
#     profile.user_id::character varying(255) AS rid,
#     NULL::character varying(255) AS act,
#     NULL::character varying(255) AS cqrs,
#     NULL::character varying(255) AS meta,
#     NULL::timestamp without time zone AS _deleted
#    FROM {schema_config.RFX_USER_SCHEMA}.profile
#   WHERE profile.organization_id IS NOT NULL AND profile.user_id IS NOT NULL
# UNION ALL
#  SELECT uuid_generate_v4() AS _id,
#     'g2'::character varying(255) AS ptype,
#     NULL::character varying(255) AS role,
#     NULL::character varying(255) AS sub,
#     "group".resource_id::character varying(255) AS org,
#     'user-profile'::character varying(255) AS dom,
#     'group'::character varying(255) AS res,
#     "group"._id::character varying(255) AS rid,
#     NULL::character varying(255) AS act,
#     NULL::character varying(255) AS cqrs,
#     NULL::character varying(255) AS meta,
#     NULL::timestamp without time zone AS _deleted
#    FROM {schema_config.RFX_USER_SCHEMA}."group"
#   WHERE "group".resource_id IS NOT NULL AND "group".resource::text = 'organization'::text
# UNION ALL
#  SELECT uuid_generate_v4() AS _id,
#     'g3'::character varying(255) AS ptype,
#     'self-access'::character varying(255) AS role,
#     "user"._id::character varying(255) AS sub,
#     NULL::character varying(255) AS org,
#     NULL::character varying(255) AS dom,
#     NULL::character varying(255) AS res,
#     NULL::character varying(255) AS rid,
#     NULL::character varying(255) AS act,
#     NULL::character varying(255) AS cqrs,
#     NULL::character varying(255) AS meta,
#     NULL::timestamp without time zone AS _deleted
#    FROM {schema_config.RFX_USER_SCHEMA}."user"
# UNION ALL
#  SELECT uuid_generate_v4() AS _id,
#     'g3'::character varying(255) AS ptype,
#     'sys-admin'::character varying(255) AS role,
#     "user"._id::character varying(255) AS sub,
#     NULL::character varying(255) AS org,
#     NULL::character varying(255) AS dom,
#     NULL::character varying(255) AS res,
#     NULL::character varying(255) AS rid,
#     NULL::character varying(255) AS act,
#     NULL::character varying(255) AS cqrs,
#     NULL::character varying(255) AS meta,
#     NULL::timestamp without time zone AS _deleted
#    FROM {schema_config.RFX_USER_SCHEMA}."user"
#   WHERE "user".is_super_admin IS TRUE
# UNION ALL
#  SELECT uuid_generate_v4() AS _id,
#     'g4'::character varying(255) AS ptype,
#     NULL::character varying(255) AS role,
#     "user"._id::character varying(255) AS sub,
#     NULL::character varying(255) AS org,
#     'user-profile'::character varying(255) AS dom,
#     'user'::character varying(255) AS res,
#     "user"._id::character varying(255) AS rid,
#     NULL::character varying(255) AS act,
#     NULL::character varying(255) AS cqrs,
#     NULL::character varying(255) AS meta,
#     NULL::timestamp without time zone AS _deleted
#    FROM {schema_config.RFX_USER_SCHEMA}."user"
# UNION ALL
#  SELECT uuid_generate_v4() AS _id,
#     'g4'::character varying(255) AS ptype,
#     NULL::character varying(255) AS role,
#     profile.user_id::character varying(255) AS sub,
#     NULL::character varying(255) AS org,
#     'user-profile'::character varying(255) AS dom,
#     'profile'::character varying(255) AS res,
#     profile._id::character varying(255) AS rid,
#     NULL::character varying(255) AS act,
#     NULL::character varying(255) AS cqrs,
#     NULL::character varying(255) AS meta,
#     NULL::timestamp without time zone AS _deleted
#    FROM {schema_config.RFX_USER_SCHEMA}.profile;
#      """
# )

# policy_idm_profile_view = PGView(
#     schema=schema_config.RFX_POLICY_SCHEMA,
#     signature="_policy__idm_profile",
#     definition=f"""
# SELECT uuid_generate_v4() AS _id,
#     'p'::character varying(255) AS ptype,
#     pol_rol.role_key AS role,
#     NULL::character varying(255) AS sub,
#     NULL::character varying(255) AS org,
#     pol_res.domain AS dom,
#     pol_res.resource AS res,
#     NULL::character varying(255) AS rid,
#     pol_res.action AS act,
#     pol_res.cqrs::character varying(255) AS cqrs,
#     concat_ws(''::text, pol_res.meta)::character varying(255) AS meta,
#     NULL::timestamp without time zone AS _deleted
#    FROM {schema_config.RFX_POLICY_SCHEMA}.policy_role pol_rol
#      JOIN {schema_config.RFX_POLICY_SCHEMA}.policy_resource pol_res ON pol_rol.policy_key::text = pol_res.policy_key::text
#   WHERE pol_res.domain::text = ANY (ARRAY['user-profile'::text, '*'::text])
# UNION ALL
#  SELECT uuid_generate_v4() AS _id,
#     'g'::character varying(255) AS ptype,
#     pro_rol.role_key AS role,
#     profile._id::character varying(255) AS sub,
#     profile.organization_id::character varying(255) AS org,
#     NULL::character varying(255) AS dom,
#     NULL::character varying(255) AS res,
#     NULL::character varying(255) AS rid,
#     NULL::character varying(255) AS act,
#     NULL::character varying(255) AS cqrs,
#     NULL::character varying(255) AS meta,
#     NULL::timestamp without time zone AS _deleted
#    FROM {schema_config.RFX_USER_SCHEMA}.profile
#      JOIN {schema_config.RFX_USER_SCHEMA}.profile_role pro_rol ON profile._id = pro_rol.profile_id
#   WHERE pro_rol._deleted IS NULL
# UNION ALL
#  SELECT uuid_generate_v4() AS _id,
#     'g2'::character varying(255) AS ptype,
#     NULL::character varying(255) AS role,
#     NULL::character varying(255) AS sub,
#     organization._id::character varying(255) AS org,
#     'user-profile'::character varying(255) AS dom,
#     'organization'::character varying(255) AS res,
#     organization._id::character varying(255) AS rid,
#     NULL::character varying(255) AS act,
#     NULL::character varying(255) AS cqrs,
#     NULL::character varying(255) AS meta,
#     NULL::timestamp without time zone AS _deleted
#    FROM {schema_config.RFX_USER_SCHEMA}.organization
# UNION ALL
#  SELECT uuid_generate_v4() AS _id,
#     'g2'::character varying(255) AS ptype,
#     NULL::character varying(255) AS role,
#     NULL::character varying(255) AS sub,
#     invitation.organization_id::character varying(255) AS org,
#     'user-profile'::character varying(255) AS dom,
#     'invitation'::character varying(255) AS res,
#     invitation._id::character varying(255) AS rid,
#     NULL::character varying(255) AS act,
#     NULL::character varying(255) AS cqrs,
#     NULL::character varying(255) AS meta,
#     NULL::timestamp without time zone AS _deleted
#    FROM {schema_config.RFX_USER_SCHEMA}.invitation
#   WHERE invitation.organization_id IS NOT NULL
# UNION ALL
#  SELECT uuid_generate_v4() AS _id,
#     'g2'::character varying(255) AS ptype,
#     NULL::character varying(255) AS role,
#     NULL::character varying(255) AS sub,
#     profile.organization_id::character varying(255) AS org,
#     'user-profile'::character varying(255) AS dom,
#     'profile'::character varying(255) AS res,
#     profile._id::character varying(255) AS rid,
#     NULL::character varying(255) AS act,
#     NULL::character varying(255) AS cqrs,
#     NULL::character varying(255) AS meta,
#     NULL::timestamp without time zone AS _deleted
#    FROM {schema_config.RFX_USER_SCHEMA}.profile
#   WHERE profile.organization_id IS NOT NULL
# UNION ALL
#  SELECT uuid_generate_v4() AS _id,
#     'g2'::character varying(255) AS ptype,
#     NULL::character varying(255) AS role,
#     NULL::character varying(255) AS sub,
#     profile.organization_id::character varying(255) AS org,
#     'user-profile'::character varying(255) AS dom,
#     'user'::character varying(255) AS res,
#     profile.user_id::character varying(255) AS rid,
#     NULL::character varying(255) AS act,
#     NULL::character varying(255) AS cqrs,
#     NULL::character varying(255) AS meta,
#     NULL::timestamp without time zone AS _deleted
#    FROM {schema_config.RFX_USER_SCHEMA}.profile
#   WHERE profile.organization_id IS NOT NULL AND profile.user_id IS NOT NULL
# UNION ALL
#  SELECT uuid_generate_v4() AS _id,
#     'g2'::character varying(255) AS ptype,
#     NULL::character varying(255) AS role,
#     NULL::character varying(255) AS sub,
#     "group".resource_id::character varying(255) AS org,
#     'user-profile'::character varying(255) AS dom,
#     'group'::character varying(255) AS res,
#     "group"._id::character varying(255) AS rid,
#     NULL::character varying(255) AS act,
#     NULL::character varying(255) AS cqrs,
#     NULL::character varying(255) AS meta,
#     NULL::timestamp without time zone AS _deleted
#    FROM {schema_config.RFX_USER_SCHEMA}."group"
#   WHERE "group".resource_id IS NOT NULL AND "group".resource::text = 'organization'::text
# UNION ALL
#  SELECT uuid_generate_v4() AS _id,
#     'g3'::character varying(255) AS ptype,
#     'self-access'::character varying(255) AS role,
#     "user"._id::character varying(255) AS sub,
#     NULL::character varying(255) AS org,
#     NULL::character varying(255) AS dom,
#     NULL::character varying(255) AS res,
#     NULL::character varying(255) AS rid,
#     NULL::character varying(255) AS act,
#     NULL::character varying(255) AS cqrs,
#     NULL::character varying(255) AS meta,
#     NULL::timestamp without time zone AS _deleted
#    FROM {schema_config.RFX_USER_SCHEMA}."user"
# UNION ALL
#  SELECT uuid_generate_v4() AS _id,
#     'g3'::character varying(255) AS ptype,
#     'sys-admin'::character varying(255) AS role,
#     "user"._id::character varying(255) AS sub,
#     NULL::character varying(255) AS org,
#     NULL::character varying(255) AS dom,
#     NULL::character varying(255) AS res,
#     NULL::character varying(255) AS rid,
#     NULL::character varying(255) AS act,
#     NULL::character varying(255) AS cqrs,
#     NULL::character varying(255) AS meta,
#     NULL::timestamp without time zone AS _deleted
#    FROM {schema_config.RFX_USER_SCHEMA}."user"
#   WHERE "user".is_super_admin IS TRUE
# UNION ALL
#  SELECT uuid_generate_v4() AS _id,
#     'g4'::character varying(255) AS ptype,
#     NULL::character varying(255) AS role,
#     "user"._id::character varying(255) AS sub,
#     NULL::character varying(255) AS org,
#     'user-profile'::character varying(255) AS dom,
#     'user'::character varying(255) AS res,
#     "user"._id::character varying(255) AS rid,
#     NULL::character varying(255) AS act,
#     NULL::character varying(255) AS cqrs,
#     NULL::character varying(255) AS meta,
#     NULL::timestamp without time zone AS _deleted
#    FROM {schema_config.RFX_USER_SCHEMA}."user"
# UNION ALL
#  SELECT uuid_generate_v4() AS _id,
#     'g4'::character varying(255) AS ptype,
#     NULL::character varying(255) AS role,
#     profile.user_id::character varying(255) AS sub,
#     NULL::character varying(255) AS org,
#     'user-profile'::character varying(255) AS dom,
#     'profile'::character varying(255) AS res,
#     profile._id::character varying(255) AS rid,
#     NULL::character varying(255) AS act,
#     NULL::character varying(255) AS cqrs,
#     NULL::character varying(255) AS meta,
#     NULL::timestamp without time zone AS _deleted
#    FROM {schema_config.RFX_USER_SCHEMA}.profile;
#      """
# )

POLICY_SCHEMA = config.RFX_POLICY_SCHEMA
USER_SCHEMA = config.RFX_USER_SCHEMA
policy_docman_view = PGView(
    schema=POLICY_SCHEMA,
    signature="_policy__docman_profile",
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
   FROM {POLICY_SCHEMA}.policy_role pol_rol
     JOIN {POLICY_SCHEMA}.policy_resource pol_res ON pol_rol.policy_key::text = pol_res.policy_key::text
  WHERE pol_res.domain::text = ANY (ARRAY['cpo-docman'::text, '*'::text])
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
   FROM {USER_SCHEMA}.profile
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
   FROM {USER_SCHEMA}.profile_role pro_rol
     JOIN {USER_SCHEMA}.profile profile ON profile._id = pro_rol.profile_id
  WHERE pro_rol._deleted IS NULL
    AND profile._deleted IS NULL
    AND profile.organization_id IS NOT NULL
    """,
)

def register_pg_entities(allow):
    register_entities(
        [
            policy_docman_view
        ]
    )

register_pg_entities(os.environ.get('REGISTER_PG_ENTITIES'))

import os
from rfx_schema import logger
from rfx_base import config

from alembic_utils.pg_view import PGView
from alembic_utils.replaceable_entity import register_entities


policy_user_profile_view = PGView(
    schema=config.RFX_POLICY_SCHEMA,
    signature="_policy__user_profile",
    definition=f"""
SELECT uuid_generate_v4() AS _id,
    'p'::character varying(255) AS ptype,
    pol_rol.role_key AS role,
    NULL::character varying(255) AS sub,
    NULL::character varying(255) AS org,
    pol_res.domain AS dom,
    pol_res.resource AS res,
    NULL::character varying(255) AS rid,
    pol_res.action AS act,
    pol_res.cqrs::character varying(255) AS cqrs,
    concat_ws(''::text, pol_res.meta)::character varying(255) AS meta,
    NULL::timestamp without time zone AS _deleted
   FROM {config.RFX_POLICY_SCHEMA}.policy_role pol_rol
     JOIN {config.RFX_POLICY_SCHEMA}.policy_resource pol_res ON pol_rol.policy_key::text = pol_res.policy_key::text
  WHERE pol_res.domain::text = 'user-profile'::text
UNION ALL
 SELECT uuid_generate_v4() AS _id,
    'g'::character varying(255) AS ptype,
    pro_rol.role_key AS role,
    profile._id::character varying(255) AS sub,
    profile.organization_id::character varying(255) AS org,
    NULL::character varying(255) AS dom,
    NULL::character varying(255) AS res,
    NULL::character varying(255) AS rid,
    NULL::character varying(255) AS act,
    NULL::character varying(255) AS cqrs,
    NULL::character varying(255) AS meta,
    NULL::timestamp without time zone AS _deleted
   FROM {config.RFX_USER_SCHEMA}.profile
     JOIN {config.RFX_USER_SCHEMA}.profile_role pro_rol ON profile._id = pro_rol.profile_id
  WHERE pro_rol._deleted IS NULL
UNION ALL
 SELECT uuid_generate_v4() AS _id,
    'g2'::character varying(255) AS ptype,
    NULL::character varying(255) AS role,
    NULL::character varying(255) AS sub,
    organization._id::character varying(255) AS org,
    'user-profile'::character varying(255) AS dom,
    'organization'::character varying(255) AS res,
    organization._id::character varying(255) AS rid,
    NULL::character varying(255) AS act,
    NULL::character varying(255) AS cqrs,
    NULL::character varying(255) AS meta,
    NULL::timestamp without time zone AS _deleted
   FROM {config.RFX_USER_SCHEMA}.organization
UNION ALL
 SELECT uuid_generate_v4() AS _id,
    'g2'::character varying(255) AS ptype,
    NULL::character varying(255) AS role,
    NULL::character varying(255) AS sub,
    invitation.organization_id::character varying(255) AS org,
    'user-profile'::character varying(255) AS dom,
    'invitation'::character varying(255) AS res,
    invitation._id::character varying(255) AS rid,
    NULL::character varying(255) AS act,
    NULL::character varying(255) AS cqrs,
    NULL::character varying(255) AS meta,
    NULL::timestamp without time zone AS _deleted
   FROM {config.RFX_USER_SCHEMA}.invitation
  WHERE invitation.organization_id IS NOT NULL
UNION ALL
 SELECT uuid_generate_v4() AS _id,
    'g2'::character varying(255) AS ptype,
    NULL::character varying(255) AS role,
    NULL::character varying(255) AS sub,
    profile.organization_id::character varying(255) AS org,
    'user-profile'::character varying(255) AS dom,
    'profile'::character varying(255) AS res,
    profile._id::character varying(255) AS rid,
    NULL::character varying(255) AS act,
    NULL::character varying(255) AS cqrs,
    NULL::character varying(255) AS meta,
    NULL::timestamp without time zone AS _deleted
   FROM {config.RFX_USER_SCHEMA}.profile
  WHERE profile.organization_id IS NOT NULL
UNION ALL
 SELECT uuid_generate_v4() AS _id,
    'g2'::character varying(255) AS ptype,
    NULL::character varying(255) AS role,
    NULL::character varying(255) AS sub,
    "group".resource_id::character varying(255) AS org,
    'user-profile'::character varying(255) AS dom,
    'group'::character varying(255) AS res,
    "group"._id::character varying(255) AS rid,
    NULL::character varying(255) AS act,
    NULL::character varying(255) AS cqrs,
    NULL::character varying(255) AS meta,
    NULL::timestamp without time zone AS _deleted
   FROM {config.RFX_USER_SCHEMA}."group"
  WHERE "group".resource_id IS NOT NULL AND "group".resource::text = 'organization'::text
UNION ALL
 SELECT uuid_generate_v4() AS _id,
    'g3'::character varying(255) AS ptype,
    'self-access'::character varying(255) AS role,
    "user"._id::character varying(255) AS sub,
    NULL::character varying(255) AS org,
    NULL::character varying(255) AS dom,
    NULL::character varying(255) AS res,
    NULL::character varying(255) AS rid,
    NULL::character varying(255) AS act,
    NULL::character varying(255) AS cqrs,
    NULL::character varying(255) AS meta,
    NULL::timestamp without time zone AS _deleted
   FROM {config.RFX_USER_SCHEMA}."user"
UNION ALL
 SELECT uuid_generate_v4() AS _id,
    'g4'::character varying(255) AS ptype,
    NULL::character varying(255) AS role,
    "user"._id::character varying(255) AS sub,
    NULL::character varying(255) AS org,
    'user-profile'::character varying(255) AS dom,
    'user'::character varying(255) AS res,
    "user"._id::character varying(255) AS rid,
    NULL::character varying(255) AS act,
    NULL::character varying(255) AS cqrs,
    NULL::character varying(255) AS meta,
    NULL::timestamp without time zone AS _deleted
   FROM {config.RFX_USER_SCHEMA}."user"
UNION ALL
 SELECT uuid_generate_v4() AS _id,
    'g4'::character varying(255) AS ptype,
    NULL::character varying(255) AS role,
    profile.user_id::character varying(255) AS sub,
    NULL::character varying(255) AS org,
    'user-profile'::character varying(255) AS dom,
    'profile'::character varying(255) AS res,
    profile._id::character varying(255) AS rid,
    NULL::character varying(255) AS act,
    NULL::character varying(255) AS cqrs,
    NULL::character varying(255) AS meta,
    NULL::timestamp without time zone AS _deleted
   FROM {config.RFX_USER_SCHEMA}.profile;
     """
)


def register_pg_entities(allow):
    allow_flag = str(allow).lower() in ("1", "true", "yes", "on")
    if not allow_flag:
        logger.info('REGISTER_PG_ENTITIES is disabled or not set.')
        return
    register_entities([
        policy_user_profile_view,
    ])

register_pg_entities(os.environ.get('REGISTER_PG_ENTITIES'))

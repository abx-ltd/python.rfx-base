CREATE OR REPLACE VIEW rfx_policy._policy__user_profile AS
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
  FROM rfx_policy.policy_role AS pol_rol
       JOIN rfx_policy.policy_resource AS pol_res ON pol_rol.policy_key::text = pol_res.policy_key::text
 WHERE pol_res.domain::text = ANY (ARRAY['user-profile'::text, '*'::text])
UNION ALL
SELECT uuid_generate_v4() AS _id,
       'g'::character varying(255) AS ptype,
       NULL::character varying(255) AS role,
       profile.user_id::character varying(255) AS usr,
       profile._id::character varying(255) AS pro,
       profile.organization_id::character varying(255) AS org,
       NULL::character varying(255) AS rid,
       'TENANT'::character varying(255) AS scope,
       NULL::character varying(255) AS act,
       NULL::character varying(255) AS cqrs,
       NULL::text AS meta,
       NULL::timestamp without time zone AS _deleted
  FROM rfx_user.profile
 WHERE profile._deleted IS NULL
   AND profile.user_id IS NOT NULL
   AND profile.organization_id IS NOT NULL
UNION ALL
SELECT uuid_generate_v4() AS _id,
       'g2'::character varying(255) AS ptype,
       pro_rol.role_key AS role,
       NULL::character varying(255) AS usr,
       profile._id::character varying(255) AS pro,
       profile.organization_id::character varying(255) AS org,
       NULL::character varying(255) AS rid,
       'TENANT'::character varying(255) AS scope,
       NULL::character varying(255) AS act,
       NULL::character varying(255) AS cqrs,
       NULL::text AS meta,
       NULL::timestamp without time zone AS _deleted
  FROM rfx_user.profile_role AS pro_rol
       JOIN rfx_user.profile ON profile._id = pro_rol.profile_id
 WHERE pro_rol._deleted IS NULL
   AND profile._deleted IS NULL
   AND profile.organization_id IS NOT NULL
UNION ALL
SELECT uuid_generate_v4() AS _id,
       'g3'::character varying(255) AS ptype,
       'self-access'::character varying(255) AS role,
       profile.user_id::character varying(255) AS usr,
       profile._id::character varying(255) AS pro,
       profile.organization_id::character varying(255) AS org,
       profile._id::character varying(255) AS rid,
       'RESOURCE'::character varying(255) AS scope,
       NULL::character varying(255) AS act,
       NULL::character varying(255) AS cqrs,
       NULL::text AS meta,
       NULL::timestamp without time zone AS _deleted
  FROM rfx_user.profile
 WHERE profile._deleted IS NULL
   AND profile.user_id IS NOT NULL;

CREATE OR REPLACE VIEW rfx_policy._policy__idm_profile AS
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
  FROM rfx_policy.policy_role AS pol_rol
       JOIN rfx_policy.policy_resource AS pol_res ON pol_rol.policy_key::text = pol_res.policy_key::text
 WHERE pol_res.domain::text = ANY (ARRAY['user-profile'::text, '*'::text])
UNION ALL
SELECT uuid_generate_v4() AS _id,
       'g'::character varying(255) AS ptype,
       NULL::character varying(255) AS role,
       profile.user_id::character varying(255) AS usr,
       profile._id::character varying(255) AS pro,
       profile.organization_id::character varying(255) AS org,
       NULL::character varying(255) AS rid,
       'TENANT'::character varying(255) AS scope,
       NULL::character varying(255) AS act,
       NULL::character varying(255) AS cqrs,
       NULL::text AS meta,
       NULL::timestamp without time zone AS _deleted
  FROM rfx_user.profile
 WHERE profile._deleted IS NULL
   AND profile.user_id IS NOT NULL
   AND profile.organization_id IS NOT NULL
UNION ALL
SELECT uuid_generate_v4() AS _id,
       'g2'::character varying(255) AS ptype,
       pro_rol.role_key AS role,
       NULL::character varying(255) AS usr,
       profile._id::character varying(255) AS pro,
       profile.organization_id::character varying(255) AS org,
       NULL::character varying(255) AS rid,
       'TENANT'::character varying(255) AS scope,
       NULL::character varying(255) AS act,
       NULL::character varying(255) AS cqrs,
       NULL::text AS meta,
       NULL::timestamp without time zone AS _deleted
  FROM rfx_user.profile_role AS pro_rol
       JOIN rfx_user.profile ON profile._id = pro_rol.profile_id
 WHERE pro_rol._deleted IS NULL
   AND profile._deleted IS NULL
   AND profile.organization_id IS NOT NULL
UNION ALL
SELECT uuid_generate_v4() AS _id,
       'g3'::character varying(255) AS ptype,
       'self-access'::character varying(255) AS role,
       profile.user_id::character varying(255) AS usr,
       profile._id::character varying(255) AS pro,
       profile.organization_id::character varying(255) AS org,
       profile._id::character varying(255) AS rid,
       'RESOURCE'::character varying(255) AS scope,
       NULL::character varying(255) AS act,
       NULL::character varying(255) AS cqrs,
       NULL::text AS meta,
       NULL::timestamp without time zone AS _deleted
  FROM rfx_user.profile
 WHERE profile._deleted IS NULL
   AND profile.user_id IS NOT NULL;

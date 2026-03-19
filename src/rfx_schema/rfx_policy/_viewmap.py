"""Policy domain no longer exposes shared views.

The policy-specific Casbin views now live within the respective domain schemas
(see `rfx_schema.rfx_user._viewmap`). This stub file is kept so imports from
`rfx_schema.rfx_policy` continue to succeed without registering duplicate view
definitions.
"""

from fluvius.query import DomainQueryManager, QuerySchema, endpoint
from fluvius.query.field import StringField, UUIDField
from .state import IDMStateManager
from .domain import UserProfileDomain


class UserProfileQueryManager(DomainQueryManager):
    __data_manager__ = IDMStateManager

    class Meta:
        api_prefix = UserProfileDomain.Meta.api_prefix
        api_tags = UserProfileDomain.Meta.api_tags


@UserProfileQueryManager.register_schema('user')
class UserQuery(QuerySchema):
    """ List current user accounts """

    class Meta(QuerySchema.Meta):
        select_all = True
        allow_item_view = False
        allow_list_view = False
        allow_meta_view = False

    _id = UUIDField("User ID", identifier=True)
    name__given = StringField("Given Name")
    name__family = StringField("Family Name")

    @endpoint(':active-profile')
    async def my_profile(request, query_manager, *args, **kwargs):
        return f"ENDPOINT: {request} {query_manager}"


@UserProfileQueryManager.register_schema('profile')
class ProfileQuery(QuerySchema):
    """ List current user's organizations """

    _id  = UUIDField("Organization ID", identifier=True)
    name = StringField("Organization Name")



@UserProfileQueryManager.register_schema('organization')
class OrganizationQuery(QuerySchema):
    """ List current user's organizations """

    _id  = UUIDField("Organization ID", identifier=True)
    name = StringField("Organization Name")
    dba_name = StringField("Business Name", source="business_name")


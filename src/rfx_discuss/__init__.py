# A Discuss attached to an aggroot without needing to be aware what is the aggroot is about
# This allow the Discuss to be attached to any item.
# See:
#    - https://areknawo.com/top-6-disqus-alternatives-for-technical-blogging/
#    - https://demo.commento.io/#commento-login-box-container


""" RFX Discuss """

from ._meta import config, logger
from .domain import RFXDiscussDomain
from .query import RFXDiscussQueryManager
from .provider import RFXDiscussProfileProvider
from . import command


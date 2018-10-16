from calendar import timegm
from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _

import graphene
from graphene.types.generic import GenericScalar

from . import exceptions
from .settings import jwt_settings
from .shortcuts import get_token
from .utils import get_payload, get_user_by_payload


class ObtainJSONWebTokenMixin(object):
    token = graphene.String()

    @classmethod
    def __init_subclass_with_meta__(cls, name=None, **options):
        assert getattr(cls, 'resolve', None), (
            '{name}.resolve method is required in a JSONWebTokenMutation.'
        ).format(name=name or cls.__name__)

        super(ObtainJSONWebTokenMixin, cls)\
            .__init_subclass_with_meta__(name=name, **options)


class ResolveMixin(object):

    @classmethod
    def resolve(cls, root, info):
        return cls()


class VerifyMixin(object):
    payload = GenericScalar()


class RefreshMixin(object):
    token = graphene.String()
    payload = GenericScalar()

    @classmethod
    def refresh(cls, root, info, token, **kwargs):
        payload = get_payload(token, info.context)
        user = get_user_by_payload(payload)
        orig_iat = payload.get('origIat')

        if orig_iat:
            utcnow = timegm(datetime.utcnow().utctimetuple())
            expiration = orig_iat +\
                jwt_settings.JWT_REFRESH_EXPIRATION_DELTA.total_seconds()

            if utcnow > expiration:
                raise exceptions.JSONWebTokenError(_('Refresh has expired'))
        else:
            raise exceptions.JSONWebTokenError(_('origIat field is required'))

        token = get_token(user, origIat=orig_iat)
        return cls(token=token, payload=payload)

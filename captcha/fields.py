from threading import local
from uuid import uuid4
from django import VERSION
from django.conf import settings
from django.utils.module_loading import import_string
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _
from django.forms.fields import MultiValueField, CharField, ValidationError
from django.forms.widgets import MultiWidget, HiddenInput, TextInput
from captcha.utils import encode_solution
from .models import CaptchaImage


CURRENT = local()
BASE_SESSION_KEY = 'HumanCheck'


def _middleware_call_wrapper(method):
    # Notes: There will ALWAYS be a method,
    #   since the method is __call__ and, if not
    #   available, we have more stuff to care
    #   about than this wrapper breaking into pieces.
    def wrapped(self, request):
        CURRENT.request = request
        result = method(self, request)
        del CURRENT.request
        return result
    return wrapped


def _middleware_process_request_wrapper(method):
    if method is None:
        def wrapped(self, request):
            CURRENT.request = request
            return None
    else:
        def wrapped(self, request):
            CURRENT.request = request
            return method(self, request)
    return wrapped


def _middleware_process_response_wrapper(method):
    if method is None:
        def wrapped(self, request, response):
            del CURRENT.request
            return response
    else:
        def wrapped(self, request, response):
            response = method(self, request, response)
            del CURRENT.request
            return response
    return wrapped


# TODO fix it to an actual condition when a version is released
# TODO where MIDDLEWARE_CLASSES is not allowed anymore.
MIDDLEWARE_CLASSES_STILL_ALLOWED = True
MIDDLEWARE_NOT_SPECIFIED = settings.MIDDLEWARE is None
MIDDLEWARE_NOT_AVAILABLE = VERSION[0:2] <= (1, 10)


if MIDDLEWARE_CLASSES_STILL_ALLOWED and (MIDDLEWARE_NOT_SPECIFIED or MIDDLEWARE_NOT_AVAILABLE):
    if not settings.MIDDLEWARE_CLASSES:
        raise ImproperlyConfigured('What the actual fuck are you doing? No middleware is configured '
                                   'under MIDDLEWARE_CLASSES')
    first_mw = import_string(settings.MIDDLEWARE_CLASSES[0])
    first_mw.process_request = _middleware_process_request_wrapper(getattr(first_mw, 'process_request', None))
    first_mw.process_response = _middleware_process_response_wrapper(getattr(first_mw, 'process_response', None))
else:
    if not settings.MIDDLEWARE:
        raise ImproperlyConfigured('What the actual fuck are you doing? No middleware is configured '
                                   'under MIDDLEWARE')
    first_mw = import_string(settings.MIDDLEWARE[0])
    first_mw.__call__ = _middleware_call_wrapper(first_mw.__call__)


class CaptchaWidget(MultiWidget):

    template_name = 'captcha/widget.html'

    def __init__(self, attrs=None):
        super(CaptchaWidget, self).__init__((HiddenInput, TextInput), attrs)

    def get_context(self, name, value, attrs):
        """
        Usually, we call .decompress(value) to have a value to render.
          However, since we don't want to use any provided value to the
          widget beforehand (the field will ALWAYS start empty), we
          override the value in the widget to be used in the context.

        Additionally, such value will be used to render an image with
          the generated captcha.
        """
        salt = attrs.pop('salt')
        key = CaptchaImage.generate(salt).key
        CURRENT.request.session[BASE_SESSION_KEY + salt] = key
        value = [key, '']
        context = super(CaptchaWidget, self).get_context(name, value, attrs)
        context.update({
            'key': context['widget']['subwidgets'][0]['value']
        })
        return context


class CaptchaField(MultiValueField):

    def compress(self, data_list):
        # Just pass the tuple
        return tuple(data_list)

    def validate(self, value):
        # The first value is the captcha's key
        # The second value is the user's input
        #
        # The user input is encoded against the field's salt to validate.
        # Also, the field must exist in user's session, so the user can never
        #   use a replay attack against the captcha.
        encoded = encode_solution(self._salt, value[1])
        if value[0] != encoded or CURRENT.request.session.get(BASE_SESSION_KEY + self._salt) != encoded:
            raise ValidationError(_('Security code was not entered properly, or has expired.'))

    def __init__(self, *args, **kwargs):
        fields = (
            CharField(),
            CharField(
                error_messages={'incomplete': 'Enter the security code.'}
            )
        )
        self._salt = str(uuid4())
        super(CaptchaField, self).__init__(fields=fields, require_all_fields=True,
                                           widget=CaptchaWidget, *args, **kwargs)

    def widget_attrs(self, widget):
        """
        Just passing the salt to the widget.
        :param widget:
        :return:
        """
        return {'salt': self._salt}

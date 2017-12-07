from PIL import Image
from django.http.response import HttpResponse
from . import models


def render_once(request, key):
    """
    Renders a specific captcha's image, and deletes it
    :param key: The sha key to render. It will be stored
                in the model.
    :return:
    """

    instance = models.CaptchaImage.objects.get(key=key)
    response = HttpResponse(content_type='image/png')
    Image.open(instance.image).save(response, "PNG")
    instance.delete()
    return response

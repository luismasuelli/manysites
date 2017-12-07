from django.conf.urls import url
from . import views

app_name = 'captcha'
urlpatterns = [
    url(r'^(\w+)$', views.render_once, name='render')
]
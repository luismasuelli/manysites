# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.utils.six import python_2_unicode_compatible
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.models import Site
from polymorphic.models import PolymorphicModel
from grimoire.django.tracked.models import TrackedLive
from grimoire.django.tracked.models.polymorphic import TrackedLive as PolymorphicTrackedLive


#######################################################################
#
# Right now this app will not be intended for the end-user but just
#   the administrative user (i.e. by using this stuff as part of the
#   Django admin; new functionality will be added to be managed inside
#   the admin interface).
#
#######################################################################


@python_2_unicode_compatible
class SiteSetting(TrackedLive):
    """
    A site setting helps us extend an existing site by adding
      configuration and children resources.

    Right now we will only consider the site being enabled, and
      the related resources, and perhaps a default resource we
      could consider as the index.
    """

    site = models.OneToOneField(Site, null=False)
    index = models.ForeignKey('SiteResource', null=True, blank=True,
                              help_text=_('Specifying an index page will make such page accessible '
                                          'as the / (root) url in the related site. The page would '
                                          'also be accessible via its url'))
    enabled = models.BooleanField(default=True, null=False,
                                  help_text=_('If you uncheck this, any resource being '
                                              'accessed for this site will raise a 404 error'))

    def clean(self):
        if self.index and self.index.setting != self:
            raise ValidationError('The specified resource as site\'s index does not '
                                  'belong to this setting')

    def __str__(self):
        return "%s' setting" % self.site


@python_2_unicode_compatible
class SiteResource(PolymorphicTrackedLive):
    """
    We will be adding these resources from the administration.

    A site resource will be related to a specific site setting we manage.
    Resources are stuff like:
      - Blogs
      - Contact Forms (synchronous), with XLS reports and mailing
      - Contact Forms (asynchronous), with XLS reports and mailing
      - Flat Pages (not using Django's but custom one)

    A site will be identified by its url_code, which is a slug.
    Such identifier serves both as internal identifier and as url chunk:

      - Aliases, Flat Pages, Forms, and Blog indexes:
          Located under /<url_code>.
      - Blog entries:
          Located under /<blog.url_code>/<id>.
      - Synchronous forms' landing pages:
          Located under /<url_code>/success.
      - Asynchronous forms' api endpoints:
          Located under /<url_code>/submit.
    """

    setting = models.ForeignKey(SiteSetting, null=False)
    url_code = models.SlugField(max_length=255, null=False, blank=False)
    title = models.CharField(max_length=127, null=False, blank=False)
    description = models.CharField(max_length=255, null=False, blank=False)
    enabled = models.BooleanField(default=True, null=False,
                                  help_text=_('If you uncheck this, this resource when being '
                                              'accessed will raise a 404 error'))

    class Meta:
        unique_together = (('setting', 'url_code'),)

    def __str__(self):
        return '%s/%s' % (self.setting.site, '' if self.setting.index == self else self.url_code)


class SiteResourceAlias(SiteResource):
    """
    An alias to be used as alternate url for a given resource.
    """

    resource = models.ForeignKey('SiteConcreteResource', null=False)

    def clean(self):
        if self.resource.setting != self.setting:
            raise ValidationError('The specified target resource must belong to the same setting')


class SiteConcreteResource(SiteResource):
    """
    A resource can be visited and keeps track of visits, if commanded in such way.

    The content is what it will show as template. Additional tags (using regular django's
      template syntax) could and will be used, and context will be provided, to render the
      appropriate content (right now this will be valid for forms and blogs).
    """

    content = models.TextField(null=False, blank=False)
    log_visits = models.BooleanField(default=False, null=False)

    @property
    def resource(self):
        """
        In contrast to aliases, this kind of site resource returns itself.
        It helps when trying to do something like:
          SiteResource.objects.get(site__domain_iexact='www.example.com', url_code='foo').resource

          and always get a SiteConcreteResource instance.

        This property is duck-typed. It does not exist in the SiteResource class.
        :return:
        """
        return self

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            last_ip = getattr(settings, 'MANYSITES_VISIT_TRACK_LAST_PROXYCHAIN_IP', False)
            ip = x_forwarded_for.split(',')[-1 if last_ip else 0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def visit(self, request):
        """
        Marks a visit to this resource, if visit logs are enabled.
        :param request: The request to take the ip from.
        :return:
        """

        if self.log_visits:
            self.visits.create(visited_from=self._get_client_ip(request))


@python_2_unicode_compatible
class SiteConcreteResourceVisit(PolymorphicModel):
    """
    A visit to the site.
    """

    resource = models.ForeignKey('SiteConcreteResource', null=False, related_name='visits')
    visited_on = models.DateTimeField(default=now, null=False)
    visited_from = models.GenericIPAddressField(null=False)

    def __str__(self):
        return '%s from %s' % (self.visited_on.strftime('%Y-%m-%d %H:%M:%S'), self.visited_from)

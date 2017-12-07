from django.utils.deprecation import MiddlewareMixin

from manysites.models import SiteResource


class SiteResourceVisitsLogger(MiddlewareMixin):

    def process_request(self, request):
        try:
            SiteResource.objects.get(sitesetting__site=request.site, url_code=request.path_info).resource.visit(request)
        except SiteResource.DoesNotExist:
            pass

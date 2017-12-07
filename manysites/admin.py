# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin
from .models import SiteSetting, SiteResource, SiteResourceAlias, SiteConcreteResource, SiteConcreteResourceVisit


class SiteSettingAdmin(admin.ModelAdmin):

    list_display = ['site', 'index', 'enabled']


class SiteResourceParentAdmin(PolymorphicParentModelAdmin):

    class SiteResourceChildAdmin(PolymorphicChildModelAdmin):
        base_model = SiteResource

    class SiteConcreteResourceChildAdmin(PolymorphicChildModelAdmin):
        base_model = SiteResource

        class SiteConcreteResourceVisitsInline(admin.TabularInline):
            model = SiteConcreteResourceVisit
            ordering = ('-visited_on',)
            fields = ('visited_on', 'visited_from')
            readonly_fields = ('visited_on', 'visited_from')

            def has_add_permission(self, request):
                return False

            def has_delete_permission(self, request, obj=None):
                return False

            def has_change_permission(self, request, obj=None):
                return True

        inlines = [SiteConcreteResourceVisitsInline]

    base_model = SiteResource
    list_display = ['__str__', 'title', 'description', 'enabled']
    child_models = (
        (SiteResourceAlias, SiteResourceChildAdmin),
        (SiteConcreteResource, SiteConcreteResourceChildAdmin)
    )


admin.site.register(SiteSetting, SiteSettingAdmin)
admin.site.register(SiteResource, SiteResourceParentAdmin)

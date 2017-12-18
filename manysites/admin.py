# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin, PolymorphicInlineModelAdmin, \
    PolymorphicInlineSupportMixin, StackedPolymorphicInline
from .models import SiteSetting, SiteResource, SiteResourceAlias, SiteConcreteResource, SiteConcreteResourceVisit, \
    SiteBundle, SiteAsset, ImageAsset, TextAsset


class SiteSettingAdmin(admin.ModelAdmin):

    list_display = ('site', 'index', 'enabled')


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
    list_display = ('__str__', 'title', 'description', 'enabled')
    child_models = (
        (SiteResourceAlias, SiteResourceChildAdmin),
        (SiteConcreteResource, SiteConcreteResourceChildAdmin)
    )


class SiteBundleAdmin(PolymorphicInlineSupportMixin, admin.ModelAdmin):

    list_display = ('__str__', 'setting', 'code', 'title', 'description')

    class SiteAssetInlineModelAdmin(StackedPolymorphicInline):
        model = SiteAsset

        class ImageAssetInlineModelAdmin(PolymorphicInlineModelAdmin.Child):
            model = ImageAsset

        class TextAssetInlineModelAdmin(PolymorphicInlineModelAdmin.Child):
            model = TextAsset

        child_inlines = (ImageAssetInlineModelAdmin, TextAssetInlineModelAdmin)

    inlines = (SiteAssetInlineModelAdmin,)


class SiteAssetAdmin(PolymorphicParentModelAdmin):

    base_model = SiteAsset
    list_display = ('__str__', 'bundle', 'code', 'preview')
    polymorphic_list = True

    class SiteAssetChildAdmin(PolymorphicChildModelAdmin):
        base_model = SiteAsset

    child_models = (
        (ImageAsset, SiteAssetChildAdmin),
        (TextAsset, SiteAssetChildAdmin)
    )

    class Media:
        css = {'all': ['manysites/css/admin.css']}

admin.site.register(SiteSetting, SiteSettingAdmin)
admin.site.register(SiteResource, SiteResourceParentAdmin)
admin.site.register(SiteBundle, SiteBundleAdmin)
admin.site.register(SiteAsset, SiteAssetAdmin)
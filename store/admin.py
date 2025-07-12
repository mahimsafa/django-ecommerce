from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth import get_user_model
from .models import Store, Config, Settings, StoreStaff

User = get_user_model()


class StoreStaffInline(admin.TabularInline):
    model = StoreStaff
    extra = 1
    fields = ('user', 'is_admin', 'accepted', 'invited_at')
    readonly_fields = ('invited_at',)
    autocomplete_fields = ('user',)


class ConfigInline(admin.StackedInline):
    model = Config
    can_delete = False
    verbose_name_plural = 'Store Configuration'
    fields = ('store', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')


class SettingsInline(admin.StackedInline):
    model = Settings
    can_delete = False
    verbose_name_plural = 'Store Settings'
    fields = ('is_active', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'tagline', 'is_active', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at', 'settings__is_active')
    search_fields = ('name', 'tagline', 'description', 'owner__username')
    date_hierarchy = 'created_at'
    inlines = [ConfigInline, SettingsInline, StoreStaffInline]
    readonly_fields = ('created_at', 'updated_at', 'logo_preview', 'thumbnail_preview')
    fieldsets = (
        ('Store Information', {
            'fields': ('name', 'tagline', 'description')
        }),
        ('Media', {
            'fields': ('logo', 'logo_preview', 'thumbnail', 'thumbnail_preview')
        }),
        ('Ownership', {
            'fields': ('owner',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def is_active(self, obj):
        return obj.settings.is_active if hasattr(obj, 'settings') else False
    is_active.boolean = True
    is_active.short_description = 'Active'

    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-height: 100px;" />',
                obj.logo.url
            )
        return "No logo"
    logo_preview.short_description = 'Logo Preview'

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="max-height: 100px;" />',
                obj.thumbnail.url
            )
        return "No thumbnail"
    thumbnail_preview.short_description = 'Thumbnail Preview'


@admin.register(StoreStaff)
class StoreStaffAdmin(admin.ModelAdmin):
    list_display = ('user', 'store', 'is_admin', 'accepted', 'invited_at')
    list_filter = ('is_admin', 'accepted', 'invited_at')
    search_fields = ('user__username', 'store__name')
    list_select_related = ('user', 'store')
    autocomplete_fields = ('user', 'store')
    readonly_fields = ('invited_at',)


@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ('store', 'created_at', 'updated_at')
    search_fields = ('store__name',)
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('store',)


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ('store', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('store__name',)
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('store',)
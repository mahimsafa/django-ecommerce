from django.contrib import admin

# Register your models here.

from .models import User, Role, RolePermission, Permission

class UserAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'created_at']
    search_fields = ['first_name', 'last_name', 'email']
    list_filter = ['created_at']

class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at', 'name']

admin.site.register(User, UserAdmin)
admin.site.register(Role)
admin.site.register(RolePermission)
admin.site.register(Permission, PermissionAdmin)

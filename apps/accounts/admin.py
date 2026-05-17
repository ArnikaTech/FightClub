from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ['phone', 'first_name', 'last_name', 'is_super_manager', 'is_club_manager', 'is_instructor', 'is_active']
    list_filter = ['is_super_manager', 'is_club_manager', 'is_instructor', 'is_active']
    search_fields = ['phone', 'first_name', 'last_name']
    fieldsets = (
        ('ورود', {'fields': ('phone', 'password')}),
        ('اطلاعات شخصی', {'fields': ('first_name', 'last_name', 'national_code', 'avatar')}),
        ('نقش‌ها', {'fields': ('is_super_manager', 'is_club_manager', 'is_instructor')}),
        ('دسترسی', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = ((None, {'fields': ('phone', 'first_name', 'last_name', 'password1', 'password2')}),)
    ordering = ['-created_at']

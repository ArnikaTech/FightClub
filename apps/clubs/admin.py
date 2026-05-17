from django.contrib import admin

from .models import Province, City, Club, ClubMembership


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin): search_fields = ['name']


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    search_fields = ['name']
    autocomplete_fields = ['province']


class MembershipInline(admin.TabularInline):
    model = ClubMembership
    extra = 0
    autocomplete_fields = ['user']


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'phone', 'is_active']
    search_fields = ['name']
    autocomplete_fields = ['province', 'city']
    inlines = [MembershipInline]


@admin.register(ClubMembership)
class ClubMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'club', 'role', 'is_active']
    autocomplete_fields = ['user', 'club']

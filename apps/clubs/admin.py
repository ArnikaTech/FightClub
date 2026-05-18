from django.contrib import admin

from .models import Province, City, Club, ClubMembership, Sport


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
    autocomplete_fields = ['province', 'city', 'sports']
    inlines = [MembershipInline]
    filter_horizontal = ['sports']


@admin.register(ClubMembership)
class ClubMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'club', 'role', 'is_active']
    autocomplete_fields = ['user', 'club']


@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['name']

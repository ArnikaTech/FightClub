from django.contrib import admin

from .models import Student, StudentContact, Insurance, Attendance


class ContactInline(admin.TabularInline):
    model = StudentContact; extra = 0


class InsuranceInline(admin.TabularInline):
    model = Insurance; extra = 0


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_code', 'user', 'club', 'current_belt', 'is_active']
    search_fields = ['student_code', 'user__first_name', 'user__last_name']
    autocomplete_fields = ['user', 'club']
    inlines = [ContactInline, InsuranceInline]


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status']
    autocomplete_fields = ['student']

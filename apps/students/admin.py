from django.contrib import admin

from .models import Student, StudentContact, Insurance, Attendance, ClassGroup, Shift, Enrollment


class ContactInline(admin.TabularInline):
    model = StudentContact; extra = 0


class InsuranceInline(admin.TabularInline):
    model = Insurance; extra = 0


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_code', 'user', 'club', 'current_belt', 'is_active']
    search_fields = ['student_code', 'user__first_name', 'user__last_name']
    autocomplete_fields = ['user', 'club', 'sport']
    inlines = [ContactInline, InsuranceInline]


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status']
    autocomplete_fields = ['student']


@admin.register(ClassGroup)
class ClassGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'club', 'sport', 'gender', 'is_active']
    search_fields = ['name']
    autocomplete_fields = ['club', 'sport']

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ['name', 'class_group', 'start_time', 'end_time', 'is_active']
    search_fields = ['name']
    autocomplete_fields = ['class_group']

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'shift', 'enrolled_at', 'is_active']
    search_fields = ['student__user__first_name', 'student__user__last_name']
    autocomplete_fields = ['student', 'shift']

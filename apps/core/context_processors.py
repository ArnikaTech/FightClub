from apps.accounts.models import Message
from apps.students.models import Student
from .models import SiteSetting
import jdatetime

def site_settings(request):
    settings = SiteSetting.get_settings()
    
    unread_count = 0
    critical_count = 0
    birthday_count = 0
    expired_insurance = 0
    
    if request.user.is_authenticated:
        # پیام‌های خوانده نشده
        unread_count = Message.objects.filter(receiver=request.user, is_read=False).count()
        
        # هنرجویان
        students = Student.objects.filter(is_active=True)
        active_organization_id = getattr(request, 'active_organization_id', None)
        if active_organization_id and request.user.is_super_manager:
            from django.db.models import Q
            students = students.filter(
                Q(club__organization_id=active_organization_id)
                | Q(club_memberships__club__organization_id=active_organization_id, club_memberships__is_active=True)
            ).distinct()
        today = jdatetime.date.today()
        
        for s in students:
            # غیبت متوالی (۳+)
            recent = s.attendances.order_by('-date')[:3]
            if len(recent) == 3 and all(a.status == 'absent' for a in recent):
                critical_count += 1
            
            # تولدی‌های امروز
            if s.birth_date and s.birth_date.month == today.month and s.birth_date.day == today.day:
                birthday_count += 1
            
            # بیمه نزدیک انقضا (۷ روز)
            if not s.has_active_insurance():
                expired_insurance += 1
    
    active_organization_id = getattr(request, 'active_organization_id', None)
    organizations = []
    selected_organization = None
    if request.user.is_authenticated and request.user.is_super_manager:
        from apps.clubs.models import Organization
        organizations = Organization.objects.filter(is_active=True).order_by('name')
        if active_organization_id:
            selected_organization = organizations.filter(pk=active_organization_id).first()

    return {
        'site_settings': settings,
        'platform_organizations': organizations,
        'active_organization': selected_organization,
        'unread_count': unread_count,
        'critical_count': critical_count,
        'birthday_count': birthday_count,
        'expired_insurance': expired_insurance,
    }
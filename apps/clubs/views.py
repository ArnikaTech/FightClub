from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Count, Q
from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.utils.text import slugify
from django.urls import reverse

from .models import Province, City, Club, Sport, Organization, OrganizationMembership
from .models import ClubMembership
from .access import managed_clubs_for, can_manage_clubs, can_manage_organization
from apps.accounts.models import User


def active_managed_clubs_for(user):
    return managed_clubs_for(user).filter(is_active=True)


def organization_people_for(organization):
    return User.objects.filter(is_active=True, is_super_manager=False).filter(
        Q(
            student_profile__club__organization=organization,
            student_profile__is_active=True,
            student_profile__club__is_active=True,
        )
        | Q(
            student_profile__club_memberships__club__organization=organization,
            student_profile__club_memberships__is_active=True,
            student_profile__is_active=True,
        )
        | Q(
            club_memberships__club__organization=organization,
            club_memberships__club__is_active=True,
            club_memberships__is_active=True,
        )
        | Q(
            organization_memberships__organization=organization,
            organization_memberships__is_active=True,
        )
    ).distinct()


def organization_manager_candidates_for(organization):
    return organization_people_for(organization).exclude(
        organization_memberships__organization=organization,
        organization_memberships__is_active=True,
        organization_memberships__role='manager',
    ).order_by('first_name', 'last_name')


def branch_manager_candidates_for(organization):
    return organization_manager_candidates_for(organization)


def access_management_redirect(organization):
    return redirect(f'{reverse("clubs:access_management")}?scope_org={organization.pk}')


# ========== استان‌ها ==========

class ProvinceListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Province
    template_name = 'clubs/province_list.html'
    context_object_name = 'provinces'
    
    def test_func(self):
        return self.request.user.is_super_manager


class ProvinceCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return self.request.user.is_super_manager
    def post(self, request):
        name = request.POST.get('name', '').strip()
        if name: Province.objects.create(name=name); messages.success(request, f'استان {name} ایجاد شد')
        return redirect('clubs:province_list')


class ProvinceEditView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return self.request.user.is_super_manager
    def post(self, request, pk):
        province = get_object_or_404(Province, pk=pk)
        name = request.POST.get('name', '').strip()
        if name: province.name = name; province.save(); messages.success(request, 'بروزرسانی شد')
        return redirect('clubs:province_list')


class ProvinceDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return self.request.user.is_super_manager
    
    def post(self, request, pk):
        province = get_object_or_404(Province, pk=pk)
        name = province.name
        
        if province.clubs.filter(is_active=True).exists():
            messages.error(request, f'استان "{name}" باشگاه فعال دارد. ابتدا باشگاه‌ها را غیرفعال کنید.')
        else:
            province.delete()
            messages.success(request, f'استان "{name}" با موفقیت حذف شد.')
        
        return redirect('clubs:province_list')

# ========== شهرها ==========

class CityListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = City
    template_name = 'clubs/city_list.html'
    context_object_name = 'cities'
    
    def test_func(self): return self.request.user.is_super_manager
    
    def get_queryset(self):
        return City.objects.select_related('province').all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['provinces'] = Province.objects.all()
        context['organizations'] = Organization.objects.filter(is_active=True).order_by('name')
        return context


class CityCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return self.request.user.is_super_manager
    def post(self, request):
        name = request.POST.get('name', '').strip()
        province_id = request.POST.get('province')
        if name and province_id:
            City.objects.create(name=name, province_id=province_id)
            messages.success(request, f'شهر {name} ایجاد شد')
        return redirect('clubs:city_list')


class CityEditView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return self.request.user.is_super_manager
    def post(self, request, pk):
        city = get_object_or_404(City, pk=pk)
        name = request.POST.get('name', '').strip()
        province_id = request.POST.get('province')
        if name and province_id:
            city.name = name
            city.province_id = province_id
            city.save()
            messages.success(request, 'شهر بروزرسانی شد')
        return redirect('clubs:city_list')


class CityDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return self.request.user.is_super_manager
    def post(self, request, pk):
        city = get_object_or_404(City, pk=pk)
        name = city.name
        if city.clubs.filter(is_active=True).exists():
            messages.error(request, f'شهر "{name}" باشگاه فعال دارد')
        else:
            city.delete()
            messages.success(request, f'شهر "{name}" حذف شد')
        return redirect('clubs:city_list')


def get_cities(request, province_id):
    cities = City.objects.filter(province_id=province_id).values('id', 'name')
    return JsonResponse(list(cities), safe=False)


# ========== مدیریت مجموعه‌ها ==========

class OrganizationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Organization
    template_name = 'clubs/organization_list.html'
    context_object_name = 'organizations'

    def test_func(self):
        return self.request.user.is_super_manager

    def get_queryset(self):
        queryset = Organization.objects.annotate(
            branch_count=Count('branches')
        ).prefetch_related('branches__city', 'branches__province').order_by('name')
        status = self.request.GET.get('status', 'all')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        self.selected_status = status if status in ('all', 'active', 'inactive') else 'all'
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_status'] = self.selected_status
        return context


class OrganizationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Organization
    template_name = 'clubs/organization_detail.html'
    context_object_name = 'organization'

    def test_func(self):
        if self.request.user.is_super_manager:
            return True
        return OrganizationMembership.objects.filter(
            user=self.request.user, organization_id=self.kwargs.get('pk'),
            is_active=True, role='manager', organization__is_active=True,
        ).exists()

    def get_queryset(self):
        queryset = Organization.objects.annotate(
            branch_count=Count('branches')
        ).prefetch_related('branches__city', 'branches__province')
        if self.request.user.is_super_manager:
            return queryset
        return queryset.filter(
            pk=self.kwargs.get('pk'), memberships__user=self.request.user,
            memberships__is_active=True, memberships__role='manager', is_active=True,
        ).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.object
        context['is_platform_owner'] = self.request.user.is_super_manager
        context['can_manage_branch_staff'] = can_manage_organization(self.request.user, organization)
        context['organization_managers'] = organization.memberships.filter(
            role='manager', is_active=True
        ).select_related('user').order_by('user__first_name', 'user__last_name')
        return context


class AccessManagementView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """One dedicated, tenant-scoped place to manage organization and branch managers."""
    template_name = 'clubs/access_management.html'

    def test_func(self):
        user = self.request.user
        return user.is_super_manager or OrganizationMembership.objects.filter(
            user=user, role='manager', is_active=True, organization__is_active=True
        ).exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_super_manager:
            organizations = Organization.objects.filter(is_active=True).order_by('name')
            selected_id = self.request.GET.get('scope_org') or getattr(self.request, 'active_organization_id', None)
        else:
            organizations = Organization.objects.filter(
                memberships__user=user, memberships__role='manager', memberships__is_active=True,
                is_active=True,
            ).order_by('name').distinct()
            selected_id = self.request.GET.get('scope_org')

        selected_organization = organizations.filter(pk=selected_id).first() if selected_id else None
        if selected_organization is None and not user.is_super_manager and organizations.count() == 1:
            selected_organization = organizations.first()

        context['access_organizations'] = organizations
        context['selected_access_organization'] = selected_organization
        context['is_platform_owner'] = user.is_super_manager
        context['can_assign_organization_manager'] = user.is_super_manager
        context['can_manage_branch_staff'] = selected_organization is not None
        if selected_organization:
            context['organization_manager_candidates'] = organization_manager_candidates_for(selected_organization)
            context['organization_managers'] = selected_organization.memberships.filter(
                role='manager', is_active=True
            ).select_related('user').order_by('user__first_name', 'user__last_name')
            context['branch_manager_candidates'] = branch_manager_candidates_for(selected_organization)
            branches = list(selected_organization.branches.all().select_related('city', 'province'))
            for branch in branches:
                branch.active_managers = list(branch.memberships.filter(
                    role='manager', is_active=True
                ).select_related('user').order_by('user__first_name', 'user__last_name'))
            context['access_branches'] = branches
        return context


class OrganizationManagerAssignView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Grant or restore organization-manager access without creating a global role."""

    def test_func(self):
        return self.request.user.is_super_manager

    def post(self, request, pk):
        organization = get_object_or_404(Organization, pk=pk, is_active=True)
        user = get_object_or_404(
            organization_manager_candidates_for(organization),
            pk=request.POST.get('user_id'),
        )
        membership, created = OrganizationMembership.objects.update_or_create(
            user=user,
            organization=organization,
            defaults={'role': 'manager', 'is_active': True},
        )
        messages.success(
            request,
            f'دسترسی مدیر مجموعه برای «{user.get_full_name()}» ' + ('اعطا شد' if created else 'فعال شد'),
        )
        return access_management_redirect(organization)


class OrganizationManagerDeactivateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Revoke only this organization's manager membership; keep the audit record."""

    def test_func(self):
        return self.request.user.is_super_manager

    def post(self, request, pk, membership_pk):
        with transaction.atomic():
            organization = get_object_or_404(
                Organization.objects.select_for_update(), pk=pk
            )
            membership = get_object_or_404(
                OrganizationMembership.objects.select_related('user'),
                pk=membership_pk,
                organization=organization,
                is_active=True,
                role='manager',
            )
            membership.is_active = False
            membership.save(update_fields=['is_active'])
            messages.success(request, f'دسترسی مدیر مجموعه برای «{membership.user.get_full_name()}» لغو شد.')
        return access_management_redirect(organization)


class BranchManagerAssignView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        organization = get_object_or_404(Organization, pk=self.kwargs['pk'], is_active=True)
        return can_manage_organization(self.request.user, organization)

    def post(self, request, pk, club_pk):
        organization = get_object_or_404(Organization, pk=pk, is_active=True)
        club = get_object_or_404(Club, pk=club_pk, organization=organization, is_active=True)
        user = get_object_or_404(
            branch_manager_candidates_for(organization),
            pk=request.POST.get('user_id'),
        )
        ClubMembership.objects.update_or_create(
            user=user, club=club,
            defaults={'role': 'manager', 'is_active': True},
        )
        messages.success(request, f'مدیر شعبهٔ «{club.name}» برای «{user.get_full_name()}» ثبت شد.')
        return access_management_redirect(organization)


class BranchManagerDeactivateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        organization = get_object_or_404(Organization, pk=self.kwargs['pk'])
        return can_manage_organization(self.request.user, organization)

    def post(self, request, pk, club_pk, membership_pk):
        organization = get_object_or_404(Organization, pk=pk)
        club = get_object_or_404(Club, pk=club_pk, organization=organization)
        membership = get_object_or_404(
            ClubMembership.objects.select_related('user'),
            pk=membership_pk, club=club, role='manager', is_active=True,
        )
        membership.is_active = False
        membership.save(update_fields=['is_active'])
        messages.success(request, f'دسترسی مدیر به شعبهٔ «{club.name}» لغو شد.')
        return access_management_redirect(organization)


class OrganizationEditView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_super_manager

    def post(self, request, pk):
        organization = get_object_or_404(Organization, pk=pk)
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'نام مجموعه الزامی است')
        else:
            organization.name = name
            organization.save(update_fields=['name'])
            messages.success(request, f'نام مجموعه به «{name}» تغییر کرد')
        return redirect('clubs:organization_list')


class OrganizationDeactivateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_super_manager

    def post(self, request, pk):
        organization = get_object_or_404(Organization, pk=pk)
        active_branches = organization.branches.filter(is_active=True).count()
        if active_branches:
            messages.error(
                request,
                f'مجموعه دارای {active_branches} شعبه فعال است. ابتدا شعبه‌های آن را غیرفعال کنید.'
            )
        else:
            organization.is_active = False
            organization.save(update_fields=['is_active'])
            messages.success(request, f'مجموعه «{organization.name}» غیرفعال شد')
        return redirect('clubs:organization_list')


class OrganizationActivateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_super_manager

    def post(self, request, pk):
        organization = get_object_or_404(Organization, pk=pk)
        if not organization.is_active:
            organization.is_active = True
            organization.save(update_fields=['is_active'])
            messages.success(request, f'مجموعه «{organization.name}» دوباره فعال شد')
        return redirect('clubs:organization_list')


class OrganizationDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_super_manager

    def post(self, request, pk):
        organization = get_object_or_404(Organization, pk=pk)
        name = organization.name
        branch_count = organization.branches.count()
        if branch_count:
            messages.error(
                request,
                f'مجموعه «{name}» دارای {branch_count} شعبه است و قابل حذف نیست. '
                'برای حفظ سوابق، ابتدا وضعیت آن را غیرفعال کنید یا شعبه‌های وابسته را تعیین تکلیف کنید.'
            )
        else:
            organization.delete()
            messages.success(request, f'مجموعه «{name}» حذف شد')
        return redirect('clubs:organization_list')


class OrganizationCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_super_manager

    def post(self, request):
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'نام مجموعه الزامی است')
            return redirect('clubs:organization_list')

        base_slug = slugify(name, allow_unicode=True) or 'organization'
        slug = base_slug
        suffix = 2
        while Organization.objects.filter(slug=slug).exists():
            slug = f'{base_slug}-{suffix}'
            suffix += 1

        organization = Organization.objects.create(name=name, slug=slug)
        messages.success(request, f'مجموعه «{organization.name}» ایجاد شد')
        return redirect('clubs:organization_list')


# ========== باشگاه‌ها ==========

class ClubListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'clubs/club_list.html'
    context_object_name = 'clubs'
    
    def test_func(self): return can_manage_clubs(self.request.user)
    
    def get_queryset(self):
        return active_managed_clubs_for(self.request.user).select_related('province', 'city')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['provinces'] = Province.objects.all()
        organizations = Organization.objects.filter(is_active=True).order_by('name')
        selected_organization_id = getattr(self.request, 'active_organization_id', None)
        if selected_organization_id:
            organizations = organizations.filter(pk=selected_organization_id)
        context['organizations'] = organizations
        return context


class ClubCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return self.request.user.is_super_manager

    def post(self, request):
        name = request.POST.get('name', '').strip()
        province_id = request.POST.get('province')
        city_id = request.POST.get('city')
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        organization_id = request.POST.get('organization')

        if not (name and province_id and city_id and organization_id):
            messages.error(request, 'نام شعبه، مجموعه، استان و شهر الزامی است')
            return redirect('clubs:club_list')

        allowed_organizations = Organization.objects.filter(is_active=True)
        selected_organization_id = getattr(request, 'active_organization_id', None)
        if selected_organization_id:
            allowed_organizations = allowed_organizations.filter(pk=selected_organization_id)
        organization = get_object_or_404(allowed_organizations, pk=organization_id)

        Club.objects.create(
            organization=organization,
            name=name,
            province_id=province_id,
            city_id=city_id,
            phone=phone,
            address=address,
        )
        messages.success(request, f'شعبه «{name}» در مجموعه «{organization.name}» ایجاد شد')
        return redirect('clubs:club_list')


class ClubEditView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return can_manage_clubs(self.request.user)

    def post(self, request, pk):
        club = get_object_or_404(managed_clubs_for(request.user), pk=pk)
        if request.user.is_super_manager:
            target_organization_id = request.POST.get('organization')
            if target_organization_id and str(target_organization_id) != str(club.organization_id):
                messages.error(
                    request,
                    'انتقال شعبه به مجموعهٔ دیگر از ویرایش عادی مجاز نیست؛ این کار ممکن است سوابق مالی و هنرجویان را جابه‌جا کند.',
                )
                return redirect('clubs:club_list')
        club.name = request.POST.get('name', '').strip()
        club.phone = request.POST.get('phone', '').strip()
        club.address = request.POST.get('address', '').strip()
        if request.user.is_super_manager:
            province_id = request.POST.get('province')
            city_id = request.POST.get('city')
            organization_id = request.POST.get('organization')
            if province_id: club.province_id = province_id
            if city_id: club.city_id = city_id
            if organization_id:
                club.organization = get_object_or_404(
                    Organization, pk=organization_id, is_active=True
                )
        club.save()
        messages.success(request, 'باشگاه بروزرسانی شد')
        return redirect('clubs:club_list')


class ClubDetailView(LoginRequiredMixin, DetailView):
    model = Club
    template_name = 'clubs/club_detail.html'
    context_object_name = 'club'

    def get_queryset(self):
        return managed_clubs_for(self.request.user)


class ClubDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return self.request.user.is_super_manager
    
    def post(self, request, pk):
        club = get_object_or_404(managed_clubs_for(request.user), pk=pk)
        name = club.name
        
        # چک کن هنرجو یا کلاس فعال داره؟
        if club.students.filter(is_active=True).exists():
            messages.error(request, f'باشگاه "{name}" هنرجوی فعال دارد. ابتدا هنرجویان را غیرفعال کنید.')
        elif club.class_groups.filter(is_active=True).exists():
            messages.error(request, f'باشگاه "{name}" کلاس فعال دارد. ابتدا کلاس‌ها را حذف کنید.')
        else:
            club.delete()
            messages.success(request, f'باشگاه "{name}" حذف شد')
        
        return redirect('clubs:club_list')


class ClubActivateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return self.request.user.is_super_manager

    def post(self, request, pk):
        club = get_object_or_404(managed_clubs_for(request.user), pk=pk)
        club.is_active = True
        club.save()
        messages.success(request, f'باشگاه {club.name} فعال شد')
        return redirect('clubs:club_list')


@login_required
def club_detail_ajax(request, pk):
    club = get_object_or_404(managed_clubs_for(request.user), pk=pk)
    coaches = club.memberships.filter(is_active=True).select_related('user')
    return JsonResponse({
        'name': club.name,
        'province': club.province.name,
        'city': club.city.name,
        'phone': club.phone,
        'address': club.address,
        'students_count': club.students.count(),
        'coaches': [{'name': m.user.get_full_name(), 'role': m.get_role_display()} for m in coaches],
    })


@login_required
def club_info_partial(request):
    club_id = request.GET.get('club')
    club = get_object_or_404(managed_clubs_for(request.user), pk=club_id)
    return render(request, 'clubs/_club_info.html', {'club': club})


# ========== مربی‌ها ==========

class CoachListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'clubs/coach_list.html'
    context_object_name = 'coaches'
    
    def test_func(self): return can_manage_clubs(self.request.user)
    
    def get_queryset(self):
        return ClubMembership.objects.filter(
            club__in=managed_clubs_for(self.request.user),
            is_active=True,
            role__in=('instructor', 'assistant'),
        ).select_related('user', 'club')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.filter(is_active=True)
        context['clubs'] = active_managed_clubs_for(self.request.user)
        return context


class CoachCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return can_manage_clubs(self.request.user)

    def post(self, request):
        user_id = request.POST.get('user_id')
        club_id = request.POST.get('club_id')
        role = request.POST.get('role', 'instructor')
        if role not in ('instructor', 'assistant'):
            messages.error(request, 'مدیر شعبه را فقط از بخش «مدیران و دسترسی‌ها» مدیریت کنید.')
            return redirect('clubs:coach_list')
        
        if user_id and club_id:
            user = get_object_or_404(User, pk=user_id)
            club = get_object_or_404(active_managed_clubs_for(request.user), pk=club_id)
            existing_membership = ClubMembership.objects.filter(user=user, club=club).first()
            if existing_membership and existing_membership.role == 'manager':
                messages.error(request, 'این کاربر مدیر شعبه است؛ برای تغییر دسترسی از بخش «مدیران و دسترسی‌ها» استفاده کنید.')
                return redirect('clubs:coach_list')
            user.is_instructor = True
            user.save()
            
            membership, created = ClubMembership.objects.get_or_create(
                user=user, club=club,
                defaults={'role': role}
            )
            if not created:
                membership.role = role
                membership.is_active = True
                membership.save()
            
            messages.success(request, f'{user.get_full_name()} اضافه شد')
        return redirect('clubs:coach_list')


class CoachEditView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return can_manage_clubs(self.request.user)

    def post(self, request, pk):
        membership = get_object_or_404(
            ClubMembership,
            pk=pk,
            club__in=managed_clubs_for(request.user),
            role__in=('instructor', 'assistant'),
        )
        user_id = request.POST.get('user_id')
        club_id = request.POST.get('club_id')
        role = request.POST.get('role')
        if role not in ('instructor', 'assistant'):
            messages.error(request, 'مدیر شعبه را فقط از بخش «مدیران و دسترسی‌ها» مدیریت کنید.')
            return redirect('clubs:coach_list')
        club = get_object_or_404(active_managed_clubs_for(request.user), pk=club_id)
        
        # چک تکراری نبودن در باشگاه جدید
        if str(membership.club_id) != str(club_id) or str(membership.user_id) != str(user_id):
            exists = ClubMembership.objects.filter(user_id=user_id, club_id=club_id).exclude(pk=pk).exists()
            if exists:
                messages.error(request, 'این کاربر قبلاً در این باشگاه عضو است')
                return redirect('clubs:coach_list')
        
        membership.user_id = user_id
        membership.club = club
        membership.role = role
        membership.save()
        messages.success(request, 'بروزرسانی شد')
        return redirect('clubs:coach_list')


class CoachDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return can_manage_clubs(self.request.user)

    def post(self, request, pk):
        membership = get_object_or_404(
            ClubMembership,
            pk=pk,
            club__in=managed_clubs_for(request.user),
            role__in=('instructor', 'assistant'),
        )
        name = membership.user.get_full_name()
        membership.is_active = False
        membership.save()
        messages.success(request, f'{name} حذف شد')
        return redirect('clubs:coach_list')


class SportListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Sport
    template_name = 'clubs/sport_list.html'
    context_object_name = 'sports'
    
    def test_func(self): return self.request.user.is_super_manager


class SportCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return self.request.user.is_super_manager
    
    def post(self, request):
        name = request.POST.get('name', '').strip()
        if name:
            Sport.objects.create(name=name)
            messages.success(request, f'رشته {name} ایجاد شد')
        return redirect('clubs:sport_list')


class SportEditView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return self.request.user.is_super_manager
    
    def post(self, request, pk):
        sport = get_object_or_404(Sport, pk=pk)
        name = request.POST.get('name', '').strip()
        if name:
            sport.name = name
            sport.save()
            messages.success(request, 'بروزرسانی شد')
        return redirect('clubs:sport_list')


class SportDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return self.request.user.is_super_manager
    
    def post(self, request, pk):
        sport = get_object_or_404(Sport, pk=pk)
        name = sport.name
        
        # چک کن توی کلاس‌ها استفاده شده
        if sport.class_groups.exists():
            messages.error(request, f'رشته "{name}" در کلاس‌ها استفاده شده. ابتدا کلاس‌ها را حذف کنید.')
        else:
            sport.delete()
            messages.success(request, f'رشته "{name}" حذف شد')
        
        return redirect('clubs:sport_list')

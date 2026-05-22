from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpResponse

from .models import Province, City, Club, Sport
from .models import ClubMembership
from apps.accounts.models import User



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


# ========== باشگاه‌ها ==========

class ClubListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'clubs/club_list.html'
    context_object_name = 'clubs'
    
    def test_func(self): return self.request.user.is_super_manager or self.request.user.is_club_manager
    
    def get_queryset(self):
        return Club.objects.filter(is_active=True).select_related('province', 'city')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['inactive_clubs'] = Club.objects.filter(is_active=False)
        context['provinces'] = Province.objects.all()
        return context


class ClubCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return self.request.user.is_super_manager
    def post(self, request):
        name = request.POST.get('name', '').strip()
        province_id = request.POST.get('province')
        city_id = request.POST.get('city')
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        if name and province_id and city_id:
            Club.objects.create(name=name, province_id=province_id, city_id=city_id, phone=phone, address=address)
            messages.success(request, f'باشگاه {name} ایجاد شد')
        return redirect('clubs:club_list')


class ClubEditView(LoginRequiredMixin, View):
    def post(self, request, pk):
        club = get_object_or_404(Club, pk=pk)
        club.name = request.POST.get('name', '').strip()
        club.phone = request.POST.get('phone', '').strip()
        club.address = request.POST.get('address', '').strip()
        province_id = request.POST.get('province')
        city_id = request.POST.get('city')
        if province_id: club.province_id = province_id
        if city_id: club.city_id = city_id
        club.save()
        messages.success(request, 'باشگاه بروزرسانی شد')
        return redirect('clubs:club_list')


class ClubDetailView(LoginRequiredMixin, DetailView):
    model = Club
    template_name = 'clubs/club_detail.html'
    context_object_name = 'club'


class ClubDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        club = get_object_or_404(Club, pk=pk)
        club.is_active = False
        club.save()
        messages.success(request, f'باشگاه {club.name} غیرفعال شد')
        return redirect('clubs:club_list')


class ClubActivateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        club = get_object_or_404(Club, pk=pk)
        club.is_active = True
        club.save()
        messages.success(request, f'باشگاه {club.name} فعال شد')
        return redirect('clubs:club_list')


def club_detail_ajax(request, pk):
    club = get_object_or_404(Club, pk=pk)
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


def club_info_partial(request):
    club_id = request.GET.get('club')
    club = get_object_or_404(Club, pk=club_id)
    return render(request, 'clubs/_club_info.html', {'club': club})


# ========== مربی‌ها ==========

class CoachListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'clubs/coach_list.html'
    context_object_name = 'coaches'
    
    def test_func(self): return self.request.user.is_super_manager or self.request.user.is_club_manager
    
    def get_queryset(self):
        return ClubMembership.objects.filter(is_active=True).select_related('user', 'club')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.filter(is_active=True)
        context['clubs'] = Club.objects.filter(is_active=True)
        return context


class CoachCreateView(LoginRequiredMixin, View):
    def post(self, request):
        user_id = request.POST.get('user_id')
        club_id = request.POST.get('club_id')
        role = request.POST.get('role', 'instructor')
        
        if user_id and club_id:
            user = get_object_or_404(User, pk=user_id)
            club = get_object_or_404(Club, pk=club_id)
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


class CoachEditView(LoginRequiredMixin, View):
    def post(self, request, pk):
        membership = get_object_or_404(ClubMembership, pk=pk)
        user_id = request.POST.get('user_id')
        club_id = request.POST.get('club_id')
        role = request.POST.get('role')
        
        # چک تکراری نبودن در باشگاه جدید
        if str(membership.club_id) != str(club_id) or str(membership.user_id) != str(user_id):
            exists = ClubMembership.objects.filter(user_id=user_id, club_id=club_id).exclude(pk=pk).exists()
            if exists:
                messages.error(request, 'این کاربر قبلاً در این باشگاه عضو است')
                return redirect('clubs:coach_list')
        
        membership.user_id = user_id
        membership.club_id = club_id
        membership.role = role
        membership.save()
        messages.success(request, 'بروزرسانی شد')
        return redirect('clubs:coach_list')


class CoachDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        membership = get_object_or_404(ClubMembership, pk=pk)
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
        sport.delete()
        messages.success(request, 'رشته حذف شد')
        return redirect('clubs:sport_list')

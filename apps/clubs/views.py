from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings

from .models import Province, City, Club
from .models import ClubMembership

User = settings.AUTH_USER_MODEL


class CoachListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'clubs/coach_list.html'
    context_object_name = 'coaches'
    
    def test_func(self):
        return self.request.user.is_super_manager or self.request.user.is_club_manager
    
    def get_queryset(self):
        return ClubMembership.objects.filter(is_active=True).select_related('user', 'club')


class CoachCreateView(LoginRequiredMixin, View):
    def get(self, request):
        from apps.accounts.models import User as UserModel
        users = UserModel.objects.filter(is_active=True)
        clubs = Club.objects.filter(is_active=True)
        return render(request, 'clubs/coach_add.html', {'users': users, 'clubs': clubs})
    
    def post(self, request):
        user_id = request.POST.get('user_id')
        club_id = request.POST.get('club_id')
        role = request.POST.get('role', 'instructor')
        
        if user_id and club_id:
            from apps.accounts.models import User as UserModel
            user = get_object_or_404(UserModel, pk=user_id)
            club = get_object_or_404(Club, pk=club_id)
            
            user.is_instructor = True
            user.save()
            
            # اگر قبلاً عضو بوده، فقط آپدیت کن
            membership = ClubMembership.objects.filter(user=user, club=club).first()
            if membership:
                membership.role = role
                membership.is_active = True
                membership.save()
            else:
                ClubMembership.objects.create(user=user, club=club, role=role)
            
            messages.success(request, f'{user.get_full_name()} به عنوان مربی اضافه شد')
            return redirect('clubs:coach_list')
        
        messages.error(request, 'همه فیلدها الزامی است')
        return redirect('clubs:coach_add')


class CoachEditView(LoginRequiredMixin, View):
    def get(self, request, pk):
        membership = get_object_or_404(ClubMembership, pk=pk)
        clubs = Club.objects.filter(is_active=True)
        return render(request, 'clubs/coach_edit.html', {'membership': membership, 'clubs': clubs})
    
    def post(self, request, pk):
        membership = get_object_or_404(ClubMembership, pk=pk)
        
        new_role = request.POST.get('role', membership.role)
        new_club_id = request.POST.get('club_id', membership.club_id)
        
        # چک کن تکراری نباشه
        if str(membership.club_id) != str(new_club_id):
            exists = ClubMembership.objects.filter(
                user=membership.user, club_id=new_club_id
            ).exclude(pk=pk).first()
            
            if exists:
                messages.error(request, 'این کاربر قبلاً در این باشگاه عضو است')
                return redirect('clubs:coach_edit', pk=pk)
        
        membership.role = new_role
        membership.club_id = new_club_id
        membership.save()
    
        messages.success(request, 'بروزرسانی شد')
        return redirect('clubs:coach_list')


class CoachDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        membership = get_object_or_404(ClubMembership, pk=pk)
        name = membership.user.get_full_name()
        membership.is_active = False
        membership.save()
        messages.success(request, f'{name} از مربیان حذف شد')
        return redirect('clubs:coach_list')


class ClubListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'clubs/club_list.html'
    context_object_name = 'clubs'
    
    def test_func(self):
        return self.request.user.is_super_manager
    
    def get_queryset(self):
        return Club.objects.filter(is_active=True).select_related('province', 'city')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['inactive_clubs'] = Club.objects.filter(is_active=False)
        return context


class ClubCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_super_manager
    
    def get(self, request):
        provinces = Province.objects.all()
        return render(request, 'clubs/club_add.html', {'provinces': provinces})
    
    def post(self, request):
        name = request.POST.get('name')
        province_id = request.POST.get('province')
        city_id = request.POST.get('city')
        phone = request.POST.get('phone', '')
        address = request.POST.get('address', '')
        
        if name and province_id and city_id:
            Club.objects.create(
                name=name,
                province_id=province_id,
                city_id=city_id,
                phone=phone,
                address=address
            )
            messages.success(request, f'باشگاه {name} ایجاد شد')
            return redirect('clubs:club_list')
        
        messages.error(request, 'نام، استان و شهر الزامی است')
        return redirect('clubs:club_add')


class ClubDetailView(LoginRequiredMixin, DetailView):
    model = Club
    template_name = 'clubs/club_detail.html'
    context_object_name = 'club'


class ClubEditView(LoginRequiredMixin, View):
    def get(self, request, pk):
        club = get_object_or_404(Club, pk=pk)
        provinces = Province.objects.all()
        cities = City.objects.filter(province=club.province)
        return render(request, 'clubs/club_edit.html', {
            'club': club, 'provinces': provinces, 'cities': cities
        })
    
    def post(self, request, pk):
        club = get_object_or_404(Club, pk=pk)
        club.name = request.POST.get('name', club.name)
        club.phone = request.POST.get('phone', club.phone)
        club.address = request.POST.get('address', club.address)
        province_id = request.POST.get('province')
        city_id = request.POST.get('city')
        if province_id: club.province_id = province_id
        if city_id: club.city_id = city_id
        club.save()
        messages.success(request, 'باشگاه بروزرسانی شد')
        return redirect('clubs:club_detail', pk=pk)


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


def get_cities(request, province_id):
    cities = City.objects.filter(province_id=province_id).values('id', 'name')
    return JsonResponse(list(cities), safe=False)


# ========== استان‌ها ==========

class ProvinceListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Province
    template_name = 'clubs/province_list.html'
    context_object_name = 'provinces'
    
    def test_func(self):
        return self.request.user.is_super_manager


class ProvinceCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_super_manager
    
    def get(self, request):
        return render(request, 'clubs/province_add.html')
    
    def post(self, request):
        name = request.POST.get('name', '').strip()
        if name:
            Province.objects.create(name=name)
            messages.success(request, f'استان {name} ایجاد شد')
            return redirect('clubs:province_list')
        messages.error(request, 'نام استان الزامی است')
        return redirect('clubs:province_add')


class ProvinceEditView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_super_manager
    
    def get(self, request, pk):
        province = get_object_or_404(Province, pk=pk)
        return render(request, 'clubs/province_edit.html', {'province': province})
    
    def post(self, request, pk):
        province = get_object_or_404(Province, pk=pk)
        name = request.POST.get('name', '').strip()
        if name:
            province.name = name
            province.save()
            messages.success(request, 'استان بروزرسانی شد')
            return redirect('clubs:province_list')
        messages.error(request, 'نام استان الزامی است')
        return redirect('clubs:province_edit', pk=pk)


# ========== شهرها ==========

class CityListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = City
    template_name = 'clubs/city_list.html'
    context_object_name = 'cities'
    
    def test_func(self):
        return self.request.user.is_super_manager
    
    def get_queryset(self):
        return City.objects.select_related('province').all()


class CityCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_super_manager
    
    def get(self, request):
        provinces = Province.objects.all()
        return render(request, 'clubs/city_add.html', {'provinces': provinces})
    
    def post(self, request):
        name = request.POST.get('name', '').strip()
        province_id = request.POST.get('province')
        if name and province_id:
            City.objects.create(name=name, province_id=province_id)
            messages.success(request, f'شهر {name} ایجاد شد')
            return redirect('clubs:city_list')
        messages.error(request, 'نام شهر و استان الزامی است')
        return redirect('clubs:city_add')


class CityEditView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_super_manager
    
    def get(self, request, pk):
        city = get_object_or_404(City, pk=pk)
        provinces = Province.objects.all()
        return render(request, 'clubs/city_edit.html', {'city': city, 'provinces': provinces})
    
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
        messages.error(request, 'نام شهر و استان الزامی است')
        return redirect('clubs:city_edit', pk=pk)


class ProvinceDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_super_manager
    
    def post(self, request, pk):
        province = get_object_or_404(Province, pk=pk)
        name = province.name
        
        # چک: آیا حتی یک باشگاه فعال در این استان هست؟
        has_active = Club.objects.filter(
            province=province,
            is_active=True
        ).exists()
        
        if has_active:
            messages.error(request, f'استان {name} باشگاه فعال دارد. ابتدا باشگاه‌ها را غیرفعال کنید.')
            return redirect('clubs:province_list')
        
        # حذف امن
        province.delete()
        messages.success(request, f'استان {name} با موفقیت حذف شد')
        return redirect('clubs:province_list')


class CityDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_super_manager
    
    def post(self, request, pk):
        city = get_object_or_404(City, pk=pk)
        name = city.name
        
        # چک: آیا حتی یک باشگاه فعال در این شهر هست؟
        has_active = Club.objects.filter(
            city=city,
            is_active=True
        ).exists()
        
        if has_active:
            messages.error(request, f'شهر {name} باشگاه فعال دارد. ابتدا باشگاه‌ها را غیرفعال کنید.')
            return redirect('clubs:city_list')
        
        city.delete()
        messages.success(request, f'شهر {name} با موفقیت حذف شد')
        return redirect('clubs:city_list')


def club_info_partial(request):
    club_id = request.GET.get('club')
    club = get_object_or_404(Club, pk=club_id)
    return render(request, 'clubs/_club_info.html', {'club': club})

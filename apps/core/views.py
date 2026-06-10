from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.templatetags.static import static
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.conf import settings as django_settings
import json

from .models import SiteSetting, SocialLink


def manifest(request):
    settings = SiteSetting.get_settings()
    app_name = settings.gym_name or 'باشگاه ستاره‌ها'
    payload = {
        'name': app_name,
        'short_name': app_name[:12],
        'description': 'سامانه مدیریت باشگاه',
        'start_url': '/',
        'scope': '/',
        'id': '/',
        'display': 'standalone',
        'display_override': ['window-controls-overlay', 'standalone', 'minimal-ui'],
        'dir': 'rtl',
        'lang': 'fa',
        'orientation': 'portrait-primary',
        'background_color': '#0a0c14',
        'theme_color': '#ff4d2e',
        'categories': ['sports', 'productivity', 'business'],
        'prefer_related_applications': False,
        'icons': [
            {
                'src': static('pwa/icons/icon-192x192.png'),
                'sizes': '192x192',
                'type': 'image/png',
                'purpose': 'any maskable',
            },
            {
                'src': static('pwa/icons/icon-512x512.png'),
                'sizes': '512x512',
                'type': 'image/png',
                'purpose': 'any maskable',
            },
        ],
        'shortcuts': [
            {
                'name': 'داشبورد',
                'short_name': 'داشبورد',
                'description': 'مشاهده داشبورد باشگاه',
                'url': '/dashboard/',
                'icons': [{'src': static('pwa/icons/icon-192x192.png'), 'sizes': '192x192'}],
            },
            {
                'name': 'هنرجویان',
                'short_name': 'هنرجویان',
                'description': 'مدیریت هنرجویان',
                'url': '/students/',
                'icons': [{'src': static('pwa/icons/icon-192x192.png'), 'sizes': '192x192'}],
            },
        ],
    }
    response = HttpResponse(
        json.dumps(payload, ensure_ascii=False),
        content_type='application/manifest+json',
    )
    response['Cache-Control'] = 'no-cache, max-age=0'
    return response


def service_worker(request):
    response = render(
        request,
        'pwa/service-worker.js',
        {'sw_version': django_settings.PWA_CACHE_VERSION},
        content_type='application/javascript',
    )
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache, max-age=0'
    return response


class SettingsView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return self.request.user.is_super_manager
    
    def get(self, request):
        settings = SiteSetting.get_settings()
        social_links = SocialLink.objects.all()
        return render(request, 'core/settings.html', {
            'settings': settings,
            'social_links': social_links,
        })
    
    def post(self, request):
        settings = SiteSetting.get_settings()
        settings.gym_name = request.POST.get('gym_name', settings.gym_name)
        settings.central_phone = request.POST.get('central_phone', '')
        settings.central_address = request.POST.get('central_address', '')
        settings.working_hours = request.POST.get('working_hours', '')
        settings.about_text = request.POST.get('about_text', '')
        settings.rules_text = request.POST.get('rules_text', '')
        
        logo = request.FILES.get('logo')
        if logo: settings.logo = logo
        
        settings.save()
        messages.success(request, 'تنظیمات بروزرسانی شد')
        return redirect('core:settings')


class SocialLinkCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return self.request.user.is_super_manager
    
    def post(self, request):
        platform = request.POST.get('platform', 'other')
        label = request.POST.get('label', '')
        url = request.POST.get('url', '')
        if url:
            SocialLink.objects.create(platform=platform, label=label, url=url)
            messages.success(request, 'شبکه اجتماعی اضافه شد')
        return redirect('core:settings')


class SocialLinkEditView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return self.request.user.is_super_manager
    
    def post(self, request, pk):
        link = get_object_or_404(SocialLink, pk=pk)
        link.platform = request.POST.get('platform', link.platform)
        link.label = request.POST.get('label', '')
        link.url = request.POST.get('url', link.url)
        link.save()
        messages.success(request, 'بروزرسانی شد')
        return redirect('core:settings')


class SocialLinkDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return self.request.user.is_super_manager
    
    def post(self, request, pk):
        link = get_object_or_404(SocialLink, pk=pk)
        link.delete()
        messages.success(request, 'حذف شد')
        return redirect('core:settings')

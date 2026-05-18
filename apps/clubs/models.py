from django.db import models
from django.conf import settings


class Province(models.Model):
    name = models.CharField('استان', max_length=100)
    
    class Meta:
        verbose_name = 'استان'
        verbose_name_plural = 'استان‌ها'
    
    def __str__(self):
        return self.name


class City(models.Model):
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name='cities', verbose_name='استان')
    name = models.CharField('شهر', max_length=100)
    
    class Meta:
        verbose_name = 'شهر'
        verbose_name_plural = 'شهرها'
    
    def __str__(self):
        return f"{self.name} - {self.province.name}"


class Club(models.Model):
    name = models.CharField('نام باشگاه', max_length=200)
    sports = models.ManyToManyField('Sport', related_name='clubs', verbose_name='رشته‌های ورزشی', blank=True)
    province = models.ForeignKey(Province, on_delete=models.PROTECT, related_name='clubs', verbose_name='استان')
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name='clubs', verbose_name='شهر')
    address = models.TextField('آدرس', blank=True, null=True)
    phone = models.CharField('تلفن', max_length=11, blank=True, null=True)
    is_active = models.BooleanField('فعال', default=True)
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)
    
    class Meta:
        verbose_name = 'باشگاه'
        verbose_name_plural = 'باشگاه‌ها'
    
    def __str__(self):
        return f"{self.name} - {self.city.name}"


class ClubMembership(models.Model):
    ROLE_CHOICES = [
        ('manager', 'مدیر'),
        ('instructor', 'مربی'),
        ('assistant', 'کمک‌مربی'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='club_memberships', verbose_name='کاربر')
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='memberships', verbose_name='باشگاه')
    role = models.CharField('نقش', max_length=20, choices=ROLE_CHOICES, default='instructor')
    is_active = models.BooleanField('فعال', default=True)
    joined_at = models.DateTimeField('تاریخ عضویت', auto_now_add=True)
    
    class Meta:
        verbose_name = 'عضو'
        verbose_name_plural = 'عضوها'
        unique_together = ['user', 'club']
    
    def __str__(self):
        return f"{self.user} - {self.club} ({self.get_role_display()})"


class Sport(models.Model):
    """رشته ورزشی"""
    name = models.CharField('نام رشته', max_length=100)
    description = models.TextField('توضیحات', blank=True, null=True)
    
    class Meta:
        verbose_name = 'رشته ورزشی'
        verbose_name_plural = 'رشته‌های ورزشی'
        ordering = ['name']
    
    def __str__(self):
        return self.name

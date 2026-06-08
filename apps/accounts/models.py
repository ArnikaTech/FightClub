from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

from django_jalali.db import models as jmodels


class UserMnaager(BaseUserManager):
    def create_user(self, phone, password=None, **extra):
        if not phone: raise ValueError('شماره همراه الزامی هست')
        
        user = self.model(phone=phone, **extra)
        user.set_password(password)
        user.save()
        
        return user
    
    def create_superuser(self, phone, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        extra.setdefault('is_super_manager', True)
        
        return self.create_user(phone, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField('شماره همراه', max_length=11, unique=True)
    first_name = models.CharField('نام', max_length=100)
    last_name = models.CharField('نام‌خانوادگی', max_length=100)
    birth_date = jmodels.jDateField('تاریخ تولد', null=True, blank=True)
    national_code = models.CharField('کد ملی', max_length=10, unique=True, null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_super_manager = models.BooleanField('مدیر کل', default=False)
    is_club_manager = models.BooleanField('مدیر باشگاه', default=False)
    is_instructor = models.BooleanField('مربی', default=False)
    is_active = models.BooleanField('فعال', default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField('تاریخ ثبت', auto_now_add=True)
    updated_at = models.DateTimeField('تاریخ ویرایش', auto_now=True)

    objects = UserMnaager()
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربرها'
    
    def __str__(self):
        return f'{self.first_name} {self.last_name}'
    
    def get_short_name(self):
        return self.first_name
    
    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages', verbose_name='فرستنده')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', verbose_name='گیرنده')
    student = models.ForeignKey('students.Student', on_delete=models.SET_NULL, null=True, blank=True, related_name='messages', verbose_name='مربوط به هنرجو')
    subject = models.CharField('موضوع', max_length=200)
    body = models.TextField('متن پیام')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies', verbose_name='پاسخ به')
    is_read = models.BooleanField('خوانده شده', default=False)
    created_at = models.DateTimeField('تاریخ', auto_now_add=True)
    
    class Meta:
        verbose_name = 'پیام'
        verbose_name_plural = 'پیام‌ها'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sender} → {self.receiver}: {self.subject}"

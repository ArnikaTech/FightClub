from django.db import models
from django.conf import settings

import jdatetime
from django_jalali.db import models as jmodels
from apps.clubs.models import Club, Sport


class Student(models.Model):
    BELTS = [
        ('white', 'سفید'),
        ('yellow', 'زرد'),
        ('orange', 'نارنجی'),
        ('green', 'سبز'),
        ('blue', 'آبی'),
        ('red', 'قرمز'),
        ('black_1', 'دان ۱'),
        ('black_2', 'دان ۲'),
        ('black_3', 'دان ۳'),
        ('black_4', 'دان ۴'),
        ('black_5', 'دان ۵'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile',
        verbose_name='کاربر'
    )
    club = models.ForeignKey(
        Club,
        on_delete=models.PROTECT,
        related_name='students',
        verbose_name='باشگاه'
    )
    sport = models.ForeignKey(Sport, on_delete=models.PROTECT, null=True, blank=True, related_name='students', verbose_name='رشته ورزشی')
    birth_date = jmodels.jDateField('تاریخ تولد', null=True, blank=True)
    student_code = models.CharField('کد هنرجویی', max_length=20, blank=True, unique=True)
    current_belt = models.CharField('کمربند فعلی', max_length=20, choices=BELTS, default='white')
    is_active = models.BooleanField('فعال', default=True)
    joined_at = jmodels.jDateField('تاریخ عضویت', auto_now_add=True)
    notes = models.TextField('یادداشت', blank=True, null=True)
    
    class Meta:
        verbose_name = 'هنرجو'
        verbose_name_plural = 'هنرجوها'
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.student_code}"
    
    def age(self):
        if self.birth_date:
            today = jdatetime.date.today()
            return today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        return None
    
    def belt_color(self):
        colors = {
            'white': '#f5f5f5',
            'yellow': '#fdd835',
            'orange': '#ff9800',
            'green': '#4caf50',
            'blue': '#2196f3',
            'red': '#f44336',
            'black_1': '#212121',
            'black_2': '#212121',
            'black_3': '#212121',
            'black_4': '#212121',
            'black_5': '#212121',
        }
        return colors.get(self.current_belt, '#f5f5f5')
    
    def is_birthday_today(self):
        if self.birth_date:
            today = jdatetime.date.today()
            return self.birth_date.month == today.month and self.birth_date.day == today.day
        return False
    
    def insurance_days_left(self):
        """روزهای باقی‌مانده تا انقضای بیمه - یا None اگر بیمه نداره یا منقضی شده"""
        last = self.insurances.first()
        if last:
            today = jdatetime.date.today()
            if last.expiry_date >= today:
                return (last.expiry_date - today).days
        return None
    
    def has_active_insurance(self):
        return self.insurance_days_left() is not None
    
    def consecutive_absences(self, days=3):
        recent = self.attendances.order_by('-date')[:days]
        if len(recent) < days:
            return 0
        return sum(1 for a in recent if a.status == 'absent')


class StudentContact(models.Model):
    TYPES = [
        ('parent', 'والدین'),
        ('emergency', 'اضطراری'),
        ('other', 'سایر'),
    ]
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='contacts',
        verbose_name='هنرجو'
    )
    phone = models.CharField('شماره تماس', max_length=11)
    contact_type = models.CharField('نوع تماس', max_length=20, choices=TYPES, default='parent')
    label = models.CharField('برچسب', max_length=100, blank=True, null=True)
    
    class Meta:
        verbose_name = 'شماره تماس'
        verbose_name_plural = 'شماره‌های تماس'
    
    def __str__(self):
        return f"{self.phone} - {self.get_contact_type_display()}"


class Insurance(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='insurances',
        verbose_name='هنرجو'
    )
    start_date = jmodels.jDateField('تاریخ شروع')
    expiry_date = jmodels.jDateField('تاریخ انقضا')
    insurance_code = models.CharField('کد بیمه', max_length=50, blank=True, null=True)
    created_at = models.DateTimeField('تاریخ ثبت', auto_now_add=True)
    
    class Meta:
        verbose_name = 'بیمه'
        verbose_name_plural = 'بیمه‌ها'
        ordering = ['-expiry_date']
    
    def __str__(self):
        return f"{self.student}: {self.start_date} تا {self.expiry_date}"
    
    @property
    def is_active(self):
        today = jdatetime.date.today()
        return self.start_date <= today <= self.expiry_date


class Attendance(models.Model):
    STATUS = [
        ('present', 'حاضر'),
        ('absent', 'غیبت'),
        ('late', 'تأخیر'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances', verbose_name='هنرجو')
    shift = models.ForeignKey('Shift', on_delete=models.PROTECT, related_name='attendances', verbose_name='شیفت', null=True, blank=True)
    date = jmodels.jDateField('تاریخ')
    status = models.CharField('وضعیت', max_length=10, choices=STATUS, default='present')
    created_at = models.DateTimeField('تاریخ ثبت', auto_now_add=True)
    
    class Meta:
        verbose_name = 'حضور و غیاب'
        verbose_name_plural = 'حضور و غیاب‌ها'
        unique_together = ['student', 'shift', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.student} - {self.date} - {self.get_status_display()}"


class ClassGroup(models.Model):
    """کلاس/گروه آموزشی"""
    GENDER_CHOICES = [
        ('male', 'آقایان'),
        ('female', 'بانوان'),
        ('mixed', 'مختلط'),
    ]
    
    club = models.ForeignKey(Club, on_delete=models.PROTECT, related_name='class_groups', verbose_name='باشگاه')
    sport = models.ForeignKey(Sport, on_delete=models.PROTECT, related_name='class_groups', verbose_name='رشته ورزشی')
    name = models.CharField('نام کلاس', max_length=200)
    gender = models.CharField('جنسیت', max_length=10, choices=GENDER_CHOICES, default='mixed')
    description = models.TextField('توضیحات', blank=True, null=True)
    is_active = models.BooleanField('فعال', default=True)
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)
    
    class Meta:
        verbose_name = 'کلاس'
        verbose_name_plural = 'کلاس‌ها'
        ordering = ['club', 'sport', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.club.name})"


class Shift(models.Model):
    """شیفت کلاس"""
    DAY_CHOICES = [
        ('saturday', 'شنبه'),
        ('sunday', 'یکشنبه'),
        ('monday', 'دوشنبه'),
        ('tuesday', 'سه‌شنبه'),
        ('wednesday', 'چهارشنبه'),
        ('thursday', 'پنج‌شنبه'),
        ('friday', 'جمعه'),
    ]
    
    class_group = models.ForeignKey(ClassGroup, on_delete=models.CASCADE, related_name='shifts', verbose_name='کلاس')
    name = models.CharField('نام شیفت', max_length=200, help_text='مثال: صبح ۸ تا ۱۰')
    days = models.CharField('روزها', max_length=200, help_text='مثال: شنبه، دوشنبه')
    start_time = models.TimeField('ساعت شروع')
    end_time = models.TimeField('ساعت پایان')
    is_active = models.BooleanField('فعال', default=True)
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)
    
    class Meta:
        verbose_name = 'شیفت'
        verbose_name_plural = 'شیفت‌ها'
        ordering = ['class_group', 'start_time']
    
    def __str__(self):
        return f"{self.name} - {self.class_group.name}"


class Enrollment(models.Model):
    """ثبت‌نام هنرجو در شیفت"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments', verbose_name='هنرجو')
    shift = models.ForeignKey(Shift, on_delete=models.PROTECT, related_name='enrollments', verbose_name='شیفت')
    enrolled_at = jmodels.jDateField('تاریخ ثبت‌نام', default=jdatetime.date.today)
    is_active = models.BooleanField('فعال', default=True)
    monthly_fee = models.PositiveIntegerField('شهریه ماهانه (تومان)', default=0)
    
    class Meta:
        verbose_name = 'ثبت‌نام'
        verbose_name_plural = 'ثبت‌نام‌ها'
        unique_together = ['student', 'shift']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} در {self.shift}"

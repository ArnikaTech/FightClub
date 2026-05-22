from django.db import models

class SiteSetting(models.Model):
    # ضروری
    gym_name = models.CharField('نام مجموعه', max_length=200, default='باشگاه ستاره‌ها')
    logo = models.ImageField('لوگو', upload_to='site/', blank=True, null=True)
    central_phone = models.CharField('شماره تماس مرکزی', max_length=11, blank=True, null=True)
    central_address = models.TextField('آدرس مرکزی', blank=True, null=True)
    
    # مفید
    about_text = models.TextField('درباره ما', blank=True, null=True)
    working_hours = models.CharField('ساعات کاری', max_length=200, blank=True, null=True, help_text='مثال: ۸ صبح تا ۱۰ شب')
    rules_text = models.TextField('شرایط عضویت', blank=True, null=True)
    
    class Meta:
        verbose_name = 'تنظیمات'
        verbose_name_plural = 'تنظیمات'
    
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
    
    def __str__(self):
        return self.gym_name


class SocialLink(models.Model):
    """شبکه‌های اجتماعی - مدیر کل هر چی خواست اضافه کنه"""
    PLATFORM_CHOICES = [
        ('instagram', 'اینستاگرام'),
        ('telegram', 'تلگرام'),
        ('whatsapp', 'واتساپ'),
        ('youtube', 'یوتیوب'),
        ('website', 'وب‌سایت'),
        ('other', 'سایر'),
    ]
    
    platform = models.CharField('پلتفرم', max_length=20, choices=PLATFORM_CHOICES, default='other')
    label = models.CharField('عنوان نمایشی', max_length=100, blank=True, null=True)
    url = models.CharField('لینک', max_length=500)
    
    class Meta:
        verbose_name = 'شبکه اجتماعی'
        verbose_name_plural = 'شبکه‌های اجتماعی'
        ordering = ['platform']
    
    def __str__(self):
        return f"{self.get_platform_display()}: {self.url}"

from django.db import models


class SiteSetting(models.Model):
    gym_name = models.CharField('نام مجموعه', max_length=200, default='آرنیکا')
    logo = models.ImageField('لوگو', upload_to='site/', blank=True, null=True)
    central_phone = models.CharField('شماره تماس مرکزی', max_length=11, blank=True, null=True)
    central_address = models.TextField('آدرس مرکزی', blank=True, null=True)    
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
    PLATFORM_CHOICES = [
        ('bale', 'بله'),
        ('eitaa', 'ایتا'),
        ('rubika', 'روبیکا'),
        ('youtube', 'یوتیوب'),
        ('telegram', 'تلگرام'),
        ('whatsapp', 'واتساپ'),
        ('website', 'وب‌سایت'),
        ('instagram', 'اینستاگرام'),
        ('other', 'سایر'),
    ]
    
    platform = models.CharField('پلتفرم', max_length=20, choices=PLATFORM_CHOICES, default='other')
    label = models.CharField('عنوان نمایشی', max_length=100, blank=True, null=True)
    url = models.CharField('لینک', max_length=500)
    
    class Meta:
        verbose_name = 'رسانه اجتماعی'
        verbose_name_plural = 'رسانه‌های اجتماعی'
        ordering = ['platform']
    
    def __str__(self):
        return f"{self.get_platform_display()}: {self.url}"

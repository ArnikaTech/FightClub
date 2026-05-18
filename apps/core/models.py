from django.db import models

class SiteSetting(models.Model):
    gym_name = models.CharField('نام مجموعه', max_length=200, default='باشگاه ستاره‌ها')
    central_phone = models.CharField('شماره تماس مرکزی', max_length=11, blank=True, null=True)
    central_address = models.TextField('آدرس مرکزی', blank=True, null=True)
    
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

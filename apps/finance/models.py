from django.db import models
from django.conf import settings
from django_jalali.db import models as jmodels
from apps.students.models import Student
from apps.clubs.models import Club


class Payment(models.Model):
    METHOD_CHOICES = [
        ('cash', 'نقدی'),
        ('card', 'کارت'),
        ('online', 'آنلاین'),
        ('other', 'سایر'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name='payments', verbose_name='هنرجو')
    amount = models.DecimalField('مبلغ (تومان)', max_digits=12, decimal_places=0)
    payment_date = jmodels.jDateField('تاریخ پرداخت')
    month = models.CharField('ماه متناظر', max_length=20)
    method = models.CharField('روش پرداخت', max_length=10, choices=METHOD_CHOICES, default='cash')
    description = models.TextField('توضیحات', blank=True, null=True)
    created_at = models.DateTimeField('تاریخ ثبت', auto_now_add=True)
    
    class Meta:
        verbose_name = 'دریافتی'
        verbose_name_plural = 'دریافتی‌ها'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.amount:,} تومان"


class Expense(models.Model):
    """هزینه - پرداختی"""
    CATEGORY_CHOICES = [
        ('rent', 'اجاره'),
        ('salary', 'حقوق'),
        ('equipment', 'تجهیزات'),
        ('utility', 'قبض'),
        ('other', 'متفرقه'),
    ]
    
    club = models.ForeignKey(Club, on_delete=models.PROTECT, related_name='expenses', verbose_name='باشگاه')
    title = models.CharField('عنوان', max_length=200)
    amount = models.DecimalField('مبلغ (تومان)', max_digits=12, decimal_places=0)
    expense_date = jmodels.jDateField('تاریخ پرداخت')
    category = models.CharField('دسته‌بندی', max_length=20, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField('توضیحات', blank=True, null=True)
    created_at = models.DateTimeField('تاریخ ثبت', auto_now_add=True)
    
    class Meta:
        verbose_name = 'پرداختی'
        verbose_name_plural = 'پرداختی‌ها'
        ordering = ['-expense_date']
    
    def __str__(self):
        return f"{self.title} - {self.amount:,} تومان"

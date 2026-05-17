from django import forms
from django.contrib.auth import get_user_model

from django_jalali.forms import jDateField
from apps.clubs.models import Club
from .models import Student

User = get_user_model()


class StudentCreateForm(forms.Form):
    """فرم ثبت هنرجوی جدید"""
    
    # اطلاعات کاربری
    first_name = forms.CharField(
        label='نام',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'input-glass', 'placeholder': 'نام'})
    )
    last_name = forms.CharField(
        label='نام خانوادگی',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'input-glass', 'placeholder': 'نام خانوادگی'})
    )
    phone = forms.CharField(
        label='شماره همراه',
        max_length=11,
        widget=forms.TextInput(attrs={'class': 'input-glass', 'placeholder': '۰۹۱۲۳۴۵۶۷۸۹'})
    )
    password = forms.CharField(
        label='گذرواژه',
        widget=forms.PasswordInput(attrs={'class': 'input-glass', 'placeholder': 'حداقل ۴ کاراکتر'})
    )
    national_code = forms.CharField(
        label='کد ملی',
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={'class': 'input-glass', 'placeholder': 'اختیاری'})
    )
    
    # اطلاعات هنرجویی
    club = forms.ModelChoiceField(
        label='باشگاه',
        queryset=Club.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'input-glass'})
    )
    birth_date = jDateField(
        label='تاریخ تولد',
        required=False,
        widget=forms.TextInput(attrs={'class': 'input-glass', 'placeholder': '۱۴۰۵/۰۲/۲۷'})
    )
    current_belt = forms.ChoiceField(
        label='کمربند فعلی',
        choices=Student.BELTS,
        widget=forms.Select(attrs={'class': 'input-glass'})
    )
    
    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError('این شماره موبایل قبلاً ثبت شده است')
        return phone
    
    def save(self):
        """ایجاد User و Student همزمان"""
        # ۱. ساخت User
        user = User.objects.create_user(
            phone=self.cleaned_data['phone'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            national_code=self.cleaned_data.get('national_code', '')
        )
        
        # ۲. تولید کد هنرجویی
        last_student = Student.objects.order_by('-id').first()
        if last_student:
            try:
                last_number = int(last_student.student_code.split('-')[-1])
                new_number = last_number + 1
            except:
                new_number = 1
        else:
            new_number = 1
        student_code = f"ST-{str(new_number).zfill(5)}"
        
        # ۳. ساخت Student
        student = Student.objects.create(
            user=user,
            club=self.cleaned_data['club'],
            birth_date=self.cleaned_data.get('birth_date'),
            student_code=student_code,
            current_belt=self.cleaned_data['current_belt']
        )
        
        return student
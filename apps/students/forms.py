from django import forms
from django.contrib.auth import get_user_model

from django_jalali.forms import jDateField
from apps.clubs.models import Club, Sport
from .models import Student, Shift, Enrollment
import jdatetime

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
        required=True,
        widget=forms.TextInput(attrs={'class': 'input-glass', 'placeholder': 'کد ملی ۱۰ رقمی'})
    )
    joined_at = forms.CharField(
        label='تاریخ عضویت',
        required=False,
        widget=forms.TextInput(attrs={'class': 'input-glass', 'placeholder': '1405/02/19'})
    )
    
    # اطلاعات هنرجویی
    club = forms.ModelChoiceField(
        label='باشگاه',
        queryset=Club.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'input-glass'})
    )
    shift = forms.ModelChoiceField(
        label='ثبت‌نام در شیفت',
        queryset=Shift.objects.filter(is_active=True, class_group__is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'input-glass'})
    )
    birth_date = forms.CharField(
        label='تاریخ تولد',
        required=False,
        widget=forms.TextInput(attrs={'class': 'input-glass', 'placeholder': '1361۰/02/19'})
    )
    current_belt = forms.ChoiceField(
        label='کمربند فعلی',
        choices=Student.BELTS,
        widget=forms.Select(attrs={'class': 'input-glass'})
    )
    sport = forms.ModelChoiceField(
        label='رشته ورزشی',
        queryset=Sport.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'input-glass'})
    )
    
    def clean_phone(self):
        phone = self.cleaned_data['phone']
        # if User.objects.filter(phone=phone).exists():
        #     raise forms.ValidationError('این شماره همراه قبلاً ثبت شده است')
        return phone
    
    def clean_birth_date(self):
        value = self.cleaned_data.get('birth_date')
        if not value:
            return None
        
        # تبدیل اعداد فارسی به انگلیسی
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        english_digits = '0123456789'
        trans = str.maketrans(persian_digits, english_digits)
        value = value.translate(trans)
        
        # پاک کردن فاصله‌ها
        value = value.replace(' ', '').replace('،', '/')
        
        try:
            parts = list(map(int, value.split('/')))
            if len(parts) != 3:
                raise ValueError
            return jdatetime.date(parts[0], parts[1], parts[2])
        except:
            raise forms.ValidationError('تاریخ معتبر وارد کنید (مثال: ۱۳۸۰/۰۱/۰۱)')
    
    def save(self):
        national_code = self.cleaned_data.get('national_code', '')
        phone = self.cleaned_data['phone']
        
        # اگر کد ملی قبلاً ثبت شده، از همون user استفاده کن
        if national_code and User.objects.filter(national_code=national_code).exists():
            user = User.objects.get(national_code=national_code)
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.phone = phone
            user.set_password(self.cleaned_data['password'])
            user.save()
        else:
            user = User.objects.create_user(
                phone=phone,
                password=self.cleaned_data['password'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                national_code=national_code or None
            )
        
        # تولید کد هنرجویی
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
        
        student = Student.objects.create(
            user=user,
            club=self.cleaned_data['club'],
            birth_date=self.cleaned_data.get('birth_date'),
            student_code=student_code,
            current_belt=self.cleaned_data['current_belt'],
            sport=self.cleaned_data.get('sport')
        )
        
        return student
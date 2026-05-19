from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, ListView, DetailView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import models

import jdatetime
from .forms import StudentCreateForm
from .models import Student, Insurance, StudentContact, Attendance
from apps.clubs.models import Club, Sport


class StudentListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    
    def test_func(self):
        user = self.request.user
        return user.is_super_manager or user.is_club_manager or user.is_instructor
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_manager:
            qs = Student.objects.filter(is_active=True).select_related('user', 'club', 'sport').prefetch_related('insurances')
        else:
            qs = Student.objects.filter(
                club__memberships__user=user,
                is_active=True
            ).select_related('user', 'club', 'sport').prefetch_related('insurances')
        
        # فیلترها
        club_id = self.request.GET.get('club')
        belt = self.request.GET.get('belt')
        sport_id = self.request.GET.get('sport')
        search = self.request.GET.get('search')
        insurance = self.request.GET.get('insurance')
        
        if club_id:
            qs = qs.filter(club_id=club_id)
        if belt:
            qs = qs.filter(current_belt=belt)
        if sport_id:
            qs = qs.filter(sport_id=sport_id)
        if search:
            qs = qs.filter(
                models.Q(user__first_name__icontains=search) |
                models.Q(user__last_name__icontains=search) |
                models.Q(user__phone__icontains=search) |
                models.Q(student_code__icontains=search)
            )
        if insurance == 'active':
            qs = qs.filter(insurances__expiry_date__gte=jdatetime.date.today())
        elif insurance == 'expired':
            qs = qs.exclude(insurances__expiry_date__gte=jdatetime.date.today())
        
        qs = qs.distinct()
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = jdatetime.date.today()
        context['clubs'] = Club.objects.filter(is_active=True)
        context['sports'] = Sport.objects.all()
        context['belt_choices'] = Student.BELTS
        return context


class StudentDetailView(LoginRequiredMixin, DetailView):
    model = Student
    template_name = 'students/student_detail.html'
    context_object_name = 'student'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = jdatetime.date.today()
        return context


class StudentCreateView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    """ثبت هنرجوی جدید"""
    template_name = 'students/student_add.html'
    form_class = StudentCreateForm
    success_url = reverse_lazy('students:student_list')
    
    def test_func(self):
        """فقط مدیر کل و مدیر باشگاه"""
        user = self.request.user
        return user.is_super_manager or user.is_club_manager
    
    def form_valid(self, form):
        student = form.save()
        messages.success(self.request, f'{student.user.get_full_name()} با موفقیت ثبت شد')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'لطفاً خطاهای فرم را بررسی کنید')
        return super().form_invalid(form)


class ContactDeleteView(LoginRequiredMixin, View):
    def post(self, request, contact_pk):
        try:
            contact = get_object_or_404(StudentContact, pk=contact_pk)
            student_pk = contact.student.pk
            contact.delete()
            messages.success(request, 'شماره تماس حذف شد')
        except Exception as e:
            messages.error(request, f'خطا در حذف شماره: {str(e)}')
            student_pk = request.POST.get('student_pk', 0)
        
        return redirect('students:student_detail', pk=student_pk)


class StudentEditView(LoginRequiredMixin, View):
    def get(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        clubs = Club.objects.filter(is_active=True)
        return render(request, 'students/student_edit.html', {
            'student': student,
            'clubs': clubs
        })
    
    def post(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        user = student.user
        
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        
        # اعتبارسنجی نام
        if not first_name or not last_name:
            messages.error(request, 'نام و نام خانوادگی الزامی است')
            return redirect('students:student_edit', pk=pk)
        
        if len(first_name) < 2 or len(last_name) < 2:
            messages.error(request, 'نام و نام خانوادگی باید حداقل ۲ کاراکتر باشد')
            return redirect('students:student_edit', pk=pk)
        
        # اعتبارسنجی تاریخ تولد
        birth_date_str = request.POST.get('birth_date', '').strip()
        if birth_date_str:
            try:
                parts = list(map(int, birth_date_str.replace('/', '-').split('-')))
                birth_date = jdatetime.date(*parts)
                today = jdatetime.date.today()
                if birth_date > today:
                    messages.error(request, 'تاریخ تولد نمی‌تواند در آینده باشد')
                    return redirect('students:student_edit', pk=pk)
                if today.year - birth_date.year > 100:
                    messages.error(request, 'تاریخ تولد نامعتبر است')
                    return redirect('students:student_edit', pk=pk)
            except:
                messages.error(request, 'فرمت تاریخ تولد نامعتبر است (مثال: ۱۳۸۰/۰۱/۰۱)')
                return redirect('students:student_edit', pk=pk)
        else:
            birth_date = student.birth_date
        
        # ذخیره
        user.first_name = first_name
        user.last_name = last_name
        user.national_code = request.POST.get('national_code', '').strip() or None
        user.save()
        
        student.birth_date = birth_date
        student.current_belt = request.POST.get('current_belt', student.current_belt)
        student.sport_id = request.POST.get('sport')
        student.club_id = request.POST.get('club', student.club_id)
        student.notes = request.POST.get('notes', '').strip()
        student.save()
        
        messages.success(request, 'اطلاعات با موفقیت بروزرسانی شد')
        return redirect('students:student_detail', pk=pk)


class InsuranceCreateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        
        start_date = request.POST.get('start_date', '').strip()
        expiry_date = request.POST.get('expiry_date', '').strip()
        
        if not start_date or not expiry_date:
            messages.error(request, 'هر دو تاریخ الزامی است')
            return redirect('students:student_detail', pk=pk)
        
        try:
            start_parts = list(map(int, start_date.replace('/', '-').split('-')))
            expiry_parts = list(map(int, expiry_date.replace('/', '-').split('-')))
            
            start = jdatetime.date(*start_parts)
            expiry = jdatetime.date(*expiry_parts)
            
            if expiry <= start:
                messages.error(request, 'تاریخ انقضا باید بعد از تاریخ شروع باشد')
                return redirect('students:student_detail', pk=pk)
            
            Insurance.objects.create(
                student=student,
                start_date=start,
                expiry_date=expiry,
            )
            messages.success(request, 'بیمه با موفقیت ثبت شد')
            
        except ValueError:
            messages.error(request, 'فرمت تاریخ نامعتبر است (مثال: ۱۴۰۳/۰۱/۰۱)')
        except Exception as e:
            messages.error(request, f'خطا در ثبت بیمه: {str(e)}')
        
        return redirect('students:student_detail', pk=pk)


class ContactCreateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        
        phone = request.POST.get('phone', '').strip()
        contact_type = request.POST.get('contact_type', 'parent')
        label = request.POST.get('label', '').strip()
        
        # اعتبارسنجی
        if not phone:
            messages.error(request, 'شماره تماس الزامی است')
            return redirect('students:student_detail', pk=pk)
        
        if not phone.isdigit():
            messages.error(request, 'شماره تماس فقط باید شامل اعداد باشد')
            return redirect('students:student_detail', pk=pk)
        
        if len(phone) < 10 or len(phone) > 11:
            messages.error(request, 'شماره تماس باید ۱۰ یا ۱۱ رقم باشد')
            return redirect('students:student_detail', pk=pk)
        
        # محدودیت تعداد مخاطب
        if student.contacts.count() >= 5:
            messages.error(request, 'حداکثر ۵ شماره تماس مجاز است')
            return redirect('students:student_detail', pk=pk)
        
        try:
            StudentContact.objects.create(
                student=student,
                phone=phone,
                contact_type=contact_type,
                label=label or None
            )
            messages.success(request, 'شماره تماس با موفقیت ثبت شد')
        except Exception as e:
            messages.error(request, f'خطا در ثبت شماره: {str(e)}')
        
        return redirect('students:student_detail', pk=pk)


class AttendanceView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """صفحه ثبت حضور و غیاب"""
    model = Student
    template_name = 'students/attendance.html'
    context_object_name = 'students'
    
    def test_func(self):
        user = self.request.user
        return user.is_super_manager or user.is_club_manager
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_manager:
            return Student.objects.filter(is_active=True).select_related('user', 'club')
        return Student.objects.filter(
            club__memberships__user=user,
            club__memberships__is_active=True,
            is_active=True
        ).select_related('user', 'club')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = jdatetime.date.today()
        context['today'] = today
        
        # هنرجویانی که امروز حاضر ثبت شدن
        attended_ids = Attendance.objects.filter(
            date=today,
            status='present'
        ).values_list('student_id', flat=True)
        context['attended_today'] = set(attended_ids)
        context['present_count'] = len(attended_ids)
        context['total_count'] = self.get_queryset().count()
        context['absent_count'] = context['total_count'] - context['present_count']
        
        return context


class AttendanceSaveView(LoginRequiredMixin, View):
    def post(self, request):
        student_ids = request.POST.getlist('student_ids')
        
        if not student_ids:
            messages.warning(request, 'هیچ هنرجویی انتخاب نشده است')
            return redirect('students:attendance')
        
        try:
            date = jdatetime.date.today()
            
            user = request.user
            if user.is_super_manager:
                students = Student.objects.filter(is_active=True)
            else:
                students = Student.objects.filter(
                    club__memberships__user=user,
                    club__memberships__is_active=True,
                    is_active=True
                )
            
            if not students.exists():
                messages.warning(request, 'هیچ هنرجوی فعالی یافت نشد')
                return redirect('students:attendance')
            
            present_count = 0
            for student in students:
                status = 'present' if str(student.id) in student_ids else 'absent'
                Attendance.objects.update_or_create(
                    student=student,
                    date=date,
                    defaults={'status': status}
                )
                if status == 'present':
                    present_count += 1
            
            messages.success(request, f'{present_count} هنرجو حاضر، {students.count() - present_count} غایب')
            
        except Exception as e:
            messages.error(request, f'خطا در ثبت حضور و غیاب: {str(e)}')
        
        return redirect('students:attendance')


class AbsenteeListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """لیست غایب‌ها"""
    template_name = 'students/absentees.html'
    context_object_name = 'absentees'
    
    def test_func(self):
        user = self.request.user
        return user.is_super_manager or user.is_club_manager
    
    def get_queryset(self):
        """هنرجویان فعال"""
        user = self.request.user
        if user.is_super_manager:
            return Student.objects.filter(is_active=True).select_related('user', 'club').prefetch_related('contacts', 'attendances')
        return Student.objects.filter(
            club__memberships__user=user,
            club__memberships__is_active=True,
            is_active=True
        ).select_related('user', 'club').prefetch_related('contacts', 'attendances')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        absentee_data = []
        for student in self.get_queryset():
            recent = student.attendances.order_by('-date')[:10]
            
            # غیبت‌های متوالی
            consecutive = 0
            for att in recent:
                if att.status == 'absent':
                    consecutive += 1
                else:
                    break
            
            # فقط غایب‌ها رو نشون بده
            if consecutive > 0:
                last_present = student.attendances.filter(status='present').order_by('-date').first()
                absentee_data.append({
                    'student': student,
                    'consecutive': consecutive,
                    'last_present_date': last_present.date if last_present else None,
                    'recent_absences': [att.date for att in recent if att.status == 'absent'][:5],
                    'contacts': student.contacts.all(),
                })
        
        # مرتب‌سازی: غیبت‌های بیشتر اول
        absentee_data.sort(key=lambda x: x['consecutive'], reverse=True)
        
        context['absentees'] = absentee_data
        context['total_absent'] = len(absentee_data)
        context['critical_count'] = sum(1 for a in absentee_data if a['consecutive'] >= 3)
        
        return context


class ContactEditView(LoginRequiredMixin, View):
    """ویرایش شماره تماس"""
    
    def get(self, request, contact_pk):
        contact = get_object_or_404(StudentContact, pk=contact_pk)
        return render(request, 'students/contact_edit.html', {'contact': contact})
    
    def post(self, request, contact_pk):
        contact = get_object_or_404(StudentContact, pk=contact_pk)
        
        phone = request.POST.get('phone', '').strip()
        contact_type = request.POST.get('contact_type', 'parent')
        label = request.POST.get('label', '').strip()
        
        if not phone or not phone.isdigit() or len(phone) < 10:
            messages.error(request, 'شماره تماس معتبر وارد کنید')
            return redirect('students:contact_edit', contact_pk=contact_pk)
        
        contact.phone = phone
        contact.contact_type = contact_type
        contact.label = label or None
        contact.save()
        
        messages.success(request, 'شماره تماس بروزرسانی شد')
        return redirect('students:student_detail', pk=contact.student.pk)

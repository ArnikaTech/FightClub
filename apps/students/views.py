from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, ListView, DetailView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy

import jdatetime
from .forms import StudentCreateForm
from .models import Student, Insurance, StudentContact, Attendance
from apps.clubs.models import Club


class StudentListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """لیست هنرجویان"""
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    
    def test_func(self):
        user = self.request.user
        return user.is_super_manager or user.is_club_manager
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_manager:
            return Student.objects.select_related('user', 'club').filter(is_active=True)
        # مدیر باشگاه فقط هنرجویان باشگاه خودش
        return Student.objects.select_related('user', 'club').filter(
            club__memberships__user=user,
            club__memberships__is_active=True,
            is_active=True
        )


class StudentDetailView(LoginRequiredMixin, DetailView):
    """جزئیات هنرجو"""
    model = Student
    template_name = 'students/student_detail.html'
    context_object_name = 'student'


class StudentCreateView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    """ثبت هنرجوی جدید"""
    template_name = 'students/student_add.html'
    form_class = StudentCreateForm
    success_url = reverse_lazy('accounts:dashboard')  # موقتاً داشبورد
    
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
        contact = get_object_or_404(StudentContact, pk=contact_pk)
        student_pk = contact.student.pk
        contact.delete()
        messages.success(request, 'شماره تماس حذف شد')
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
        
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.national_code = request.POST.get('national_code', user.national_code)
        user.save()
        
        student.birth_date = request.POST.get('birth_date') or student.birth_date
        student.current_belt = request.POST.get('current_belt', student.current_belt)
        student.club_id = request.POST.get('club', student.club_id)
        student.notes = request.POST.get('notes', student.notes)
        student.save()
        
        messages.success(request, 'اطلاعات بروزرسانی شد')
        return redirect('students:student_detail', pk=pk)


class InsuranceCreateView(LoginRequiredMixin, View):
    """ثبت بیمه برای هنرجو"""
    
    def post(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        
        start_date = request.POST.get('start_date')
        expiry_date = request.POST.get('expiry_date')
        
        if start_date and expiry_date:
            try:
                start_parts = list(map(int, start_date.replace('/', '-').split('-')))
                expiry_parts = list(map(int, expiry_date.replace('/', '-').split('-')))
                
                Insurance.objects.create(
                    student=student,
                    start_date=jdatetime.date(*start_parts),
                    expiry_date=jdatetime.date(*expiry_parts),
                )
                messages.success(request, 'بیمه با موفقیت ثبت شد')
            except:
                messages.error(request, 'تاریخ نامعتبر است')
        else:
            messages.error(request, 'هر دو تاریخ الزامی است')
        
        return redirect('students:student_detail', pk=pk)


class ContactCreateView(LoginRequiredMixin, View):
    """ثبت شماره تماس والدین"""
    
    def post(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        
        phone = request.POST.get('phone')
        contact_type = request.POST.get('contact_type', 'parent')
        label = request.POST.get('label', '')
        
        if phone and len(phone) >= 10:
            StudentContact.objects.create(
                student=student,
                phone=phone,
                contact_type=contact_type,
                label=label
            )
            messages.success(request, 'شماره تماس با موفقیت ثبت شد')
        else:
            messages.error(request, 'شماره تماس معتبر وارد کنید')
        
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
    """ذخیره حضور و غیاب"""
    
    def post(self, request):
        student_ids = request.POST.getlist('student_ids')
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
        return redirect('students:attendance')

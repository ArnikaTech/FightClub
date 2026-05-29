from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, View, ListView, DetailView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import models

import jdatetime
from .forms import StudentCreateForm
from .models import Student, Insurance, StudentContact, Attendance, ClassGroup, Shift, Enrollment
from apps.clubs.models import Club, Sport


class StudentListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    paginate_by = 20
    
    def test_func(self):
        user = self.request.user
        return user.is_super_manager or user.is_club_manager or user.is_instructor
    
    def get_queryset(self):
        user = self.request.user
        show = self.request.GET.get('show', 'active')
        
        if user.is_super_manager:
            qs = Student.objects.filter(is_active=(show == 'active')).select_related('user', 'club', 'sport').prefetch_related('insurances')
        else:
            qs = Student.objects.filter(
                club__memberships__user=user,
                is_active=(show == 'active')
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


class StudentActivateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        student.is_active = True
        student.save()
        messages.success(request, f'{student.user.get_full_name()} فعال شد')
        return redirect('students:student_list')


class StudentDetailView(LoginRequiredMixin, DetailView):
    model = Student
    template_name = 'students/student_detail.html'
    context_object_name = 'student'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = jdatetime.date.today()
        return context


class StudentEditView(LoginRequiredMixin, View):
    def get(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        club_id = request.GET.get('club', student.club_id)
        selected_club = Club.objects.get(pk=club_id) if Club.objects.filter(pk=club_id).exists() else student.club
        
        clubs = Club.objects.filter(is_active=True)
        sports = Sport.objects.all()
        belts = Student.BELTS
        
        return render(request, 'students/student_edit.html', {
            'student': student,
            'clubs': clubs,
            'sports': sports,
            'belts': belts,
            'selected_club': selected_club,
        })
    
    def post(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        user = student.user
        
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        
        if not first_name or not last_name:
            messages.error(request, 'نام و نام خانوادگی الزامی است')
            return redirect('students:student_edit', pk=pk)
        
        user.first_name = first_name
        user.last_name = last_name
        user.national_code = request.POST.get('national_code', '').strip() or None
        
        birth_date_str = request.POST.get('birth_date', '').strip()
        if birth_date_str:
            try:
                parts = list(map(int, birth_date_str.replace('/', '-').split('-')))
                student.birth_date = jdatetime.date(*parts)
            except:
                messages.error(request, 'تاریخ تولد نامعتبر است')
                return redirect('students:student_edit', pk=pk)
        
        student.club_id = request.POST.get('club', student.club_id)
        student.sport_id = request.POST.get('sport') or None
        student.current_belt = request.POST.get('current_belt', student.current_belt)
        student.notes = request.POST.get('notes', '').strip()
        
        if request.user.is_super_manager:
            user.is_instructor = request.POST.get('is_instructor') == 'on'
            user.is_club_manager = request.POST.get('is_club_manager') == 'on'
        
        user.save()
        student.save()
        messages.success(request, 'اطلاعات با موفقیت بروزرسانی شد')
        return redirect('students:student_detail', pk=pk)


class StudentCreateView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'students/student_add.html'
    form_class = StudentCreateForm
    success_url = reverse_lazy('students:student_list')
    
    def test_func(self):
        user = self.request.user
        return user.is_super_manager or user.is_club_manager
    
    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'هنرجو با موفقیت ثبت شد')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = jdatetime.date.today()
        return context


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


class AttendanceView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'students/attendance.html'
    
    def test_func(self):
        return self.request.user.is_super_manager or self.request.user.is_club_manager
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # تاریخ
        date_str = self.request.GET.get('date', '')
        if date_str:
            try:
                parts = list(map(int, date_str.replace('/', '-').split('-')))
                today = jdatetime.date(*parts)
            except:
                today = jdatetime.date.today()
        else:
            today = jdatetime.date.today()
        
        context['today'] = today
        context['shifts'] = Shift.objects.filter(is_active=True, class_group__is_active=True).select_related('class_group')
        
        shift_id = self.request.GET.get('shift')
        if shift_id:
            shift = get_object_or_404(Shift, pk=shift_id)
            context['selected_shift'] = shift
            
            # فقط هنرجویانی که قبل از تاریخ انتخاب شده ثبت‌نام کردن
            enrollments = Enrollment.objects.filter(
                shift=shift, is_active=True,
                enrolled_at__lte=today
            )

            students = [e.student for e in enrollments]
            
            attended_ids = Attendance.objects.filter(
                shift=shift, date=today, status='present'
            ).values_list('student_id', flat=True)
            
            context['students'] = students
            context['attended_today'] = set(attended_ids)
            context['present_count'] = len(attended_ids)
            context['total_count'] = len(students)
            context['absent_count'] = len(students) - len(attended_ids)
        else:
            context['students'] = []
            context['attended_today'] = set()
            context['present_count'] = 0
            context['total_count'] = 0
            context['absent_count'] = 0
        
        return context


class AttendanceSaveView(LoginRequiredMixin, View):
    def post(self, request):
        import json
        student_ids_str = request.POST.get('student_ids', '[]')
        shift_id = request.POST.get('shift')
        date_str = request.POST.get('date')
        
        try:
            student_ids = json.loads(student_ids_str)
        except:
            student_ids = []
        
        if not shift_id:
            messages.error(request, 'شیفت را انتخاب کنید')
            return redirect('students:attendance')
        
        shift = get_object_or_404(Shift, pk=shift_id)
        
        # تاریخ
        if date_str:
            try:
                parts = list(map(int, date_str.replace('/', '-').split('-')))
                date = jdatetime.date(*parts)
            except:
                date = jdatetime.date.today()
        else:
            date = jdatetime.date.today()
        
        enrollments = Enrollment.objects.filter(shift=shift, is_active=True)
        
        for enrollment in enrollments:
            status = 'present' if enrollment.student_id in student_ids else 'absent'
            Attendance.objects.update_or_create(
                student=enrollment.student,
                shift=shift,
                date=date,
                defaults={'status': status}
            )
        
        messages.success(request, f'حضور و غیاب {shift.name} ثبت شد')
        return redirect(f'/students/attendance/?shift={shift_id}&date={date_str or ""}')


class AttendanceToggleView(LoginRequiredMixin, View):
    def post(self, request, student_id):
        student = get_object_or_404(Student, pk=student_id)
        today = jdatetime.date.today()
        
        att, created = Attendance.objects.get_or_create(
            student=student, date=today,
            defaults={'status': 'absent'}
        )
        att.status = 'absent' if att.status == 'present' else 'present'
        att.save()
        
        # آمار جدید
        user = request.user
        if user.is_super_manager:
            total = Student.objects.filter(is_active=True).count()
        else:
            total = Student.objects.filter(club__memberships__user=user, is_active=True).distinct().count()
        present = Attendance.objects.filter(date=today, status='present').count()
        absent = total - present
        
        return render(request, 'students/_attendance_item.html', {
            'student': student,
            'status': att.status,
            'present_count': present,
            'absent_count': absent,
            'total_count': total,
        })


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


class AttendanceHistoryView(LoginRequiredMixin, TemplateView):
    template_name = 'students/attendance_history.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = jdatetime.date.today()
        
        year = int(self.request.GET.get('year', str(today.year)).replace(',', ''))
        month = int(self.request.GET.get('month', str(today.month)).replace(',', ''))
        shift_id = self.request.GET.get('shift')
        student_id = self.request.GET.get('student')
        
        # روزهای ماه
        if month <= 6: last_day = 31
        elif month <= 11: last_day = 30
        else: last_day = 29 if year % 4 != 0 else 30
        
        context['year'] = year
        context['month'] = month
        context['month_name'] = f'{year}/{month:02d}'
        context['days'] = list(range(1, last_day + 1))
        context['months'] = list(range(1, 13))
        context['years'] = list(range(today.year - 2, today.year + 1))
        
        # همه هنرجویان (برای فیلتر)
        if user.is_super_manager:
            all_students = Student.objects.filter(is_active=True).select_related('user')
            all_shifts = Shift.objects.filter(is_active=True).select_related('class_group')
        elif user.is_club_manager:
            clubs = Club.objects.filter(memberships__user=user, is_active=True)
            all_students = Student.objects.filter(club__in=clubs, is_active=True).select_related('user')
            all_shifts = Shift.objects.filter(class_group__club__in=clubs, is_active=True).select_related('class_group')
        else:
            all_students = Student.objects.filter(pk=user.student_profile.pk).select_related('user')
            all_shifts = Shift.objects.none()
        
        context['all_students'] = all_students
        context['all_shifts'] = all_shifts
        
        # فیلترها
        students = all_students
        shift = None
        if shift_id:
            shift = get_object_or_404(Shift, pk=shift_id)
            enrolled_ids = Enrollment.objects.filter(shift=shift, is_active=True).values_list('student_id', flat=True)
            students = students.filter(pk__in=enrolled_ids)
        if student_id:
            students = students.filter(pk=student_id)
        
        context['shift'] = shift
        context['students'] = students
        
        # جدول
        if students.exists():
            attendance_data = {}
            for s in students:
                atts = Attendance.objects.filter(student=s, date__gte=jdatetime.date(year, month, 1), date__lte=jdatetime.date(year, month, last_day))
                if shift: atts = atts.filter(shift=shift)
                att_dict = {}
                for att in atts: att_dict[att.date.day] = att.status
                attendance_data[s.id] = att_dict
            context['attendance_data'] = attendance_data
        
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


class StudentDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        student.is_active = False
        student.save()
        messages.success(request, f'{student.user.get_full_name()} غیرفعال شد')
        return redirect('students:student_list')


class ClassGroupActivateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        class_group = get_object_or_404(ClassGroup, pk=pk)
        class_group.is_active = True
        class_group.save()
        messages.success(request, f'کلاس {class_group.name} فعال شد')
        return redirect('students:class_list')


class ClassGroupListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = ClassGroup
    template_name = 'students/class_list.html'
    context_object_name = 'classes'
    
    def test_func(self):
        return self.request.user.is_super_manager or self.request.user.is_club_manager
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_manager:
            return ClassGroup.objects.filter(is_active=True).select_related('club', 'sport')
        return ClassGroup.objects.filter(
            club__memberships__user=user, is_active=True
        ).select_related('club', 'sport').distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['inactive_classes'] = ClassGroup.objects.filter(is_active=False)    
        context['clubs'] = Club.objects.filter(is_active=True)
        context['sports'] = Sport.objects.all()
        return context


class ClassGroupCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_super_manager or self.request.user.is_club_manager
    
    def post(self, request):
        name = request.POST.get('name', '').strip()
        club_id = request.POST.get('club')
        sport_id = request.POST.get('sport')
        gender = request.POST.get('gender', 'mixed')
        description = request.POST.get('description', '')
        
        if name and club_id and sport_id:
            ClassGroup.objects.create(
                name=name, club_id=club_id, sport_id=sport_id,
                gender=gender, description=description
            )
            messages.success(request, f'کلاس {name} ایجاد شد')
        else:
            messages.error(request, 'نام، باشگاه و رشته الزامی است')
        return redirect('students:class_list')


class ClassGroupEditView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_super_manager or self.request.user.is_club_manager
    
    def post(self, request, pk):
        class_group = get_object_or_404(ClassGroup, pk=pk)
        class_group.name = request.POST.get('name', class_group.name).strip()
        class_group.club_id = request.POST.get('club', class_group.club_id)
        class_group.sport_id = request.POST.get('sport', class_group.sport_id)
        class_group.gender = request.POST.get('gender', class_group.gender)
        class_group.description = request.POST.get('description', '')
        class_group.save()
        messages.success(request, 'کلاس بروزرسانی شد')
        return redirect('students:class_list')


class ClassGroupDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_super_manager or self.request.user.is_club_manager
    
    def post(self, request, pk):
        class_group = get_object_or_404(ClassGroup, pk=pk)
        class_group.is_active = False
        class_group.save()
        messages.success(request, f'کلاس {class_group.name} غیرفعال شد')
        return redirect('students:class_list')


class ShiftActivateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        shift = get_object_or_404(Shift, pk=pk)
        shift.is_active = True
        shift.save()
        messages.success(request, f'شیفت {shift.name} فعال شد')
        return redirect('students:shift_list', class_id=shift.class_group_id)


class ShiftListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'students/shift_list.html'
    context_object_name = 'shifts'
    
    def test_func(self):
        return self.request.user.is_super_manager or self.request.user.is_club_manager
    
    def get_queryset(self):
        self.class_group = get_object_or_404(ClassGroup, pk=self.kwargs['class_id'])
        return self.class_group.shifts.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['class_group'] = self.class_group
        context['inactive_shifts'] = self.class_group.shifts.filter(is_active=False)
        return context


class ShiftCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_super_manager or self.request.user.is_club_manager
    
    def post(self, request, class_id):
        class_group = get_object_or_404(ClassGroup, pk=class_id)
        name = request.POST.get('name', '').strip()
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        
        # جمع‌آوری روزهای انتخاب شده
        days_list = []
        day_names = ['saturday', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        day_labels = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه']
        
        for i, day in enumerate(day_names):
            if request.POST.get(f'day_{day}'):
                days_list.append(day_labels[i])
        
        days = '، '.join(days_list) if days_list else request.POST.get('days', '')
        
        if name and days and start_time and end_time:
            Shift.objects.create(
                class_group=class_group, name=name, days=days,
                start_time=start_time, end_time=end_time
            )
            messages.success(request, f'شیفت {name} ایجاد شد')
        else:
            messages.error(request, 'همه فیلدها الزامی است')
        return redirect('students:shift_list', class_id=class_id)


class ShiftEditView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_super_manager or self.request.user.is_club_manager
    
    def post(self, request, pk):
        shift = get_object_or_404(Shift, pk=pk)
        shift.name = request.POST.get('name', shift.name).strip()
        shift.days = request.POST.get('days', shift.days).strip()
        shift.start_time = request.POST.get('start_time') or shift.start_time
        shift.end_time = request.POST.get('end_time') or shift.end_time
        shift.save()
        messages.success(request, 'شیفت بروزرسانی شد')
        return redirect('students:shift_list', class_id=shift.class_group_id)


class ShiftDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_super_manager or self.request.user.is_club_manager
    
    def post(self, request, pk):
        shift = get_object_or_404(Shift, pk=pk)
        class_id = shift.class_group_id
        shift.is_active = False
        shift.save()
        messages.success(request, 'شیفت غیرفعال شد')
        return redirect('students:shift_list', class_id=class_id)


class EnrollmentActivateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        enrollment = get_object_or_404(Enrollment, pk=pk)
        enrollment.is_active = True
        enrollment.save()
        messages.success(request, f'ثبت‌نام {enrollment.student.user.get_full_name()} فعال شد')
        return redirect('students:enrollment_list')


class EnrollmentListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'students/enrollment_list.html'
    context_object_name = 'enrollments'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_super_manager or self.request.user.is_club_manager
    
    def get_queryset(self):
        return Enrollment.objects.filter(is_active=True).select_related(
            'student__user', 'student__club', 'shift__class_group__sport', 'shift__class_group__club'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['students'] = Student.objects.filter(is_active=True).select_related('user', 'club')
        context['shifts'] = Shift.objects.filter(is_active=True, class_group__is_active=True).select_related('class_group')
        context['inactive_enrollments'] = Enrollment.objects.filter(is_active=False).select_related(
            'student__user', 'student__club', 'shift__class_group__sport', 'shift__class_group__club'
        )
        return context


class EnrollmentCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_super_manager or self.request.user.is_club_manager
    
    def post(self, request):
        student_id = request.POST.get('student')
        shift_id = request.POST.get('shift')
        monthly_fee = request.POST.get('monthly_fee', '0').replace(',', '')
        enrolled_at_str = request.POST.get('enrolled_at', '')
        
        # تاریخ ثبت‌نام
        if enrolled_at_str:
            try:
                parts = list(map(int, enrolled_at_str.replace('/', '-').split('-')))
                enrolled_at = jdatetime.date(*parts)
            except:
                enrolled_at = jdatetime.date.today()
        else:
            enrolled_at = jdatetime.date.today()
        
        if student_id and shift_id:
            student = get_object_or_404(Student, pk=student_id)
            shift = get_object_or_404(Shift, pk=shift_id)
            
            old_enrollment = Enrollment.objects.filter(student=student, shift=shift).first()
            if old_enrollment:
                if old_enrollment.is_active:
                    messages.error(request, 'این هنرجو قبلاً در این شیفت ثبت‌نام شده')
                else:
                    old_enrollment.is_active = True
                    old_enrollment.monthly_fee = int(monthly_fee) if monthly_fee else 0
                    old_enrollment.enrolled_at = enrolled_at
                    old_enrollment.save()
                    messages.success(request, f'{student.user.get_full_name()} مجدداً در {shift.name} ثبت‌نام شد')
            else:
                Enrollment.objects.create(
                    student=student, shift=shift,
                    monthly_fee=int(monthly_fee) if monthly_fee else 0,
                    enrolled_at=enrolled_at
                )
                messages.success(request, f'{student.user.get_full_name()} در {shift.name} ثبت‌نام شد')
        else:
            messages.error(request, 'هنرجو و شیفت را انتخاب کنید')
        return redirect('students:enrollment_list')


class EnrollmentEditView(LoginRequiredMixin, View):
    def post(self, request, pk):
        enrollment = get_object_or_404(Enrollment, pk=pk)
        shift_id = request.POST.get('shift')
        monthly_fee = request.POST.get('monthly_fee', '0').replace(',', '')
        enrolled_at_str = request.POST.get('enrolled_at', '')
        
        if shift_id:
            if str(enrollment.shift_id) != str(shift_id):
                exists = Enrollment.objects.filter(student=enrollment.student, shift_id=shift_id).exclude(pk=pk).exists()
                if exists:
                    messages.error(request, 'این هنرجو قبلاً در این شیفت ثبت‌نام شده')
                    return redirect('students:enrollment_list')
            enrollment.shift_id = shift_id
        
        if monthly_fee:
            enrollment.monthly_fee = int(monthly_fee)
        
        if enrolled_at_str:
            try:
                parts = list(map(int, enrolled_at_str.replace('/', '-').split('-')))
                enrollment.enrolled_at = jdatetime.date(*parts)
            except:
                pass
        
        enrollment.save()
        messages.success(request, 'ثبت‌نام بروزرسانی شد')
        return redirect('students:enrollment_list')


class EnrollmentDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_super_manager or self.request.user.is_club_manager
    
    def post(self, request, pk):
        enrollment = get_object_or_404(Enrollment, pk=pk)
        enrollment.is_active = False
        enrollment.save()
        messages.success(request, f'ثبت‌نام {enrollment.student.user.get_full_name()} لغو شد')
        return redirect('students:enrollment_list')

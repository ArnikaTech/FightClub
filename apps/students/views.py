from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, View, ListView, DetailView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import models, transaction

import jdatetime
from .forms import StudentCreateForm
from .models import Student, StudentClub, Insurance, StudentContact, Attendance, ClassGroup, Shift, Enrollment
from apps.clubs.models import Club, OrganizationMembership, Sport
from apps.finance.models import FeeDue, Payment


def managed_clubs_for(user):
    if user.is_super_manager:
        return Club.objects.all()
    if user.is_club_manager:
        return Club.objects.filter(
            organization__memberships__user=user,
            organization__memberships__is_active=True,
            organization__memberships__role='manager',
            organization__is_active=True,
        ).distinct()
    if user.is_instructor:
        return Club.objects.filter(memberships__user=user, memberships__is_active=True).distinct()
    return Club.objects.none()


def visible_students_for(user):
    if hasattr(user, 'student_profile'):
        own_student = Student.objects.filter(pk=user.student_profile.pk)
    else:
        own_student = Student.objects.none()
    if user.is_super_manager:
        return Student.objects.all()
    if user.is_club_manager or user.is_instructor:
        return Student.objects.filter(club_memberships__club__in=managed_clubs_for(user), club_memberships__is_active=True).distinct() | own_student
    return own_student


def managed_students_for(user):
    if user.is_super_manager:
        return Student.objects.all()
    if user.is_club_manager or user.is_instructor:
        return Student.objects.filter(club_memberships__club__in=managed_clubs_for(user), club_memberships__is_active=True).distinct()
    return Student.objects.none()


def can_manage_students(user):
    return user.is_super_manager or user.is_club_manager


def can_manage_attendance(user):
    return user.is_super_manager or user.is_club_manager


def visible_shifts_for(user):
    if user.is_super_manager:
        return Shift.objects.all()
    if user.is_club_manager or user.is_instructor:
        return Shift.objects.filter(class_group__club__in=managed_clubs_for(user)).distinct()
    return Shift.objects.none()


class StudentListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    paginate_by = 20
    
    def test_func(self):
        user = self.request.user
        return user.is_super_manager or user.is_club_manager or user.is_instructor
    
    def get_queryset(self):
        user = self.request.user
        qs = managed_students_for(user).order_by(
            'user__first_name', 'user__last_name'
        )

        # به‌صورت پیش‌فرض فقط هنرجویان فعال نمایش داده می‌شوند.
        status = self.request.GET.get('status', 'active')
        if status == 'inactive':
            qs = qs.filter(is_active=False)
        elif status != 'all':
            qs = qs.filter(is_active=True)
        
        # فیلترها
        club_id = self.request.GET.get('club')
        belt = self.request.GET.get('belt')
        sport_id = self.request.GET.get('sport')
        search = self.request.GET.get('search')
        insurance = self.request.GET.get('insurance')
        
        if club_id:
            qs = qs.filter(club_memberships__club_id=club_id, club_memberships__is_active=True)
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
        context['current_month'] = f"{jdatetime.date.today().year}/{jdatetime.date.today().month:02d}"
        context['clubs'] = managed_clubs_for(self.request.user).filter(is_active=True)
        context['sports'] = Sport.objects.all()
        context['belt_choices'] = Student.BELTS

        # محاسبه ماه‌های پرداخت‌نشده هنرجویان همین صفحه
        page_students = list(context['students'])
        student_ids = [student.id for student in page_students]
        enrollments = Enrollment.objects.filter(
            student_id__in=student_ids,
            is_active=True,
            student__is_active=True,
        ).values_list('student_id', 'enrolled_at')

        start_indexes = {}
        for student_id, enrolled_at in enrollments:
            index = enrolled_at.year * 12 + enrolled_at.month - 1
            if student_id not in start_indexes or index < start_indexes[student_id]:
                start_indexes[student_id] = index

        today = jdatetime.date.today()
        end_index = today.year * 12 + today.month - 1
        month_ranges = {
            student_id: [
                f'{index // 12}/{index % 12 + 1:02d}'
                for index in range(start_index, end_index + 1)
            ]
            for student_id, start_index in start_indexes.items()
            if start_index <= end_index
        }
        all_months = set(month for months in month_ranges.values() for month in months)

        paid_pairs = set()
        if student_ids and all_months:
            paid_pairs.update(
                FeeDue.objects.filter(
                    student_id__in=student_ids,
                    month__in=all_months,
                    is_paid=True,
                ).values_list('student_id', 'month')
            )
            paid_pairs.update(
                Payment.objects.filter(
                    student_id__in=student_ids,
                    month__in=all_months,
                ).values_list('student_id', 'month')
            )

        for student in page_students:
            student.unpaid_months = [
                month for month in month_ranges.get(student.id, [])
                if (student.id, month) not in paid_pairs
            ]
            student.unpaid_month_count = len(student.unpaid_months)

        return context


class StudentActivateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return can_manage_students(self.request.user)

    def post(self, request, pk):
        student = get_object_or_404(managed_students_for(request.user), pk=pk)
        if not student.is_active:
            student.is_active = True
            student.save(update_fields=['is_active'])
            messages.success(request, f'عضویت {student.user.get_full_name()} دوباره فعال شد')
        else:
            messages.info(request, 'این هنرجو در حال حاضر فعال است')
        return redirect('students:student_detail', pk=pk)


class StudentDetailView(LoginRequiredMixin, DetailView):
    model = Student
    template_name = 'students/student_detail.html'
    context_object_name = 'student'

    def get_queryset(self):
        return visible_students_for(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = jdatetime.date.today()
        if self.request.user.is_super_manager or self.request.user.is_club_manager or self.request.user.is_instructor:
            context['club_memberships'] = self.object.club_memberships.filter(
                club__in=managed_clubs_for(self.request.user)
            ).select_related('club', 'club__city', 'club__province')
        else:
            context['club_memberships'] = self.object.club_memberships.select_related(
                'club', 'club__city', 'club__province'
            ).all()
        return context


class StudentEditView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return can_manage_students(self.request.user)

    def get(self, request, pk):
        student = get_object_or_404(managed_students_for(request.user), pk=pk)
        clubs = managed_clubs_for(request.user).filter(is_active=True).select_related('city', 'province')
        memberships = student.club_memberships.filter(
            club__in=clubs
        ).select_related('club', 'club__city', 'club__province').order_by('-is_active', 'club__name')
        enrolled_club_ids = set(
            Enrollment.objects.filter(
                student=student, is_active=True
            ).values_list('shift__class_group__club_id', flat=True)
        )
        shifts = visible_shifts_for(request.user).filter(
            is_active=True, class_group__is_active=True
        ).select_related('class_group', 'class_group__club')
        return render(request, 'students/student_edit.html', {
            'student': student,
            'clubs': clubs,
            'memberships': memberships,
            'enrolled_club_ids': enrolled_club_ids,
            'available_clubs': clubs.exclude(
                pk__in=memberships.values_list('club_id', flat=True)
            ),
            'shifts': shifts,
            'sports': Sport.objects.all(),
            'belts': Student.BELTS,
            'selected_club': student.club,
        })

    def post(self, request, pk):
        student = get_object_or_404(managed_students_for(request.user), pk=pk)
        user = student.user
        allowed_clubs = managed_clubs_for(request.user)
        allowed_club_ids = set(allowed_clubs.values_list('pk', flat=True))

        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        if not first_name or not last_name:
            messages.error(request, 'نام و نام خانوادگی الزامی است')
            return redirect('students:student_edit', pk=pk)

        add_ids = request.POST.getlist('add_clubs')
        deactivate_ids = request.POST.getlist('deactivate_memberships')
        try:
            add_ids = {int(value) for value in add_ids}
            deactivate_ids = {int(value) for value in deactivate_ids}
        except (TypeError, ValueError):
            messages.error(request, 'اطلاعات عضویت باشگاه نامعتبر است')
            return redirect('students:student_edit', pk=pk)

        active_allowed_club_ids = set(
            allowed_clubs.filter(is_active=True).values_list('pk', flat=True)
        )
        if not add_ids.issubset(active_allowed_club_ids):
            messages.error(request, 'فقط می‌توانید هنرجو را به باشگاه‌های فعال و مجاز خود اضافه کنید')
            return redirect('students:student_edit', pk=pk)

        memberships = {
            membership.pk: membership
            for membership in student.club_memberships.select_related('club')
        }
        if not deactivate_ids.issubset(set(memberships)):
            messages.error(request, 'یکی از عضویت‌های انتخاب‌شده معتبر نیست')
            return redirect('students:student_edit', pk=pk)
        if any(memberships[mid].club_id not in allowed_club_ids for mid in deactivate_ids):
            messages.error(request, 'اجازه مدیریت یکی از عضویت‌های انتخاب‌شده را ندارید')
            return redirect('students:student_edit', pk=pk)

        requested_deactivations = [
            memberships[membership_id]
            for membership_id in deactivate_ids
            if memberships[membership_id].is_active
        ]
        remaining_active_ids = {
            membership.club_id
            for membership in memberships.values()
            if membership.is_active and membership.pk not in deactivate_ids
        } | add_ids
        if not remaining_active_ids:
            messages.error(request, 'هنرجو باید دست‌کم در یک باشگاه عضویت فعال داشته باشد')
            return redirect('students:student_edit', pk=pk)

        for membership in requested_deactivations:
            if Enrollment.objects.filter(
                student=student,
                shift__class_group__club_id=membership.club_id,
                is_active=True,
            ).exists():
                messages.error(
                    request,
                    f'عضویت باشگاه «{membership.club.name}» به دلیل وجود ثبت‌نام فعال قابل غیرفعال‌سازی نیست؛ '
                    'ابتدا ثبت‌نام فعال آن باشگاه را تعیین تکلیف کنید.'
                )
                return redirect('students:student_edit', pk=pk)

        new_shift = None
        new_shift_id = request.POST.get('new_shift')
        if new_shift_id:
            new_shift = get_object_or_404(
                visible_shifts_for(request.user), pk=new_shift_id,
                is_active=True, class_group__is_active=True
            )
            if new_shift.class_group.club_id not in remaining_active_ids:
                messages.error(request, 'برای ثبت‌نام در این شیفت ابتدا باید عضویت باشگاه مربوطه فعال باشد')
                return redirect('students:student_edit', pk=pk)

        birth_date_str = request.POST.get('birth_date', '').strip()
        birth_date = student.birth_date
        if birth_date_str:
            try:
                parts = list(map(int, birth_date_str.replace('/', '-').split('-')))
                birth_date = jdatetime.date(*parts)
            except (TypeError, ValueError):
                messages.error(request, 'تاریخ تولد نامعتبر است')
                return redirect('students:student_edit', pk=pk)

        joined_at_str = request.POST.get('joined_at', '').strip()
        joined_at = student.joined_at
        if joined_at_str:
            try:
                parts = list(map(int, joined_at_str.replace('/', '-').split('-')))
                joined_at = jdatetime.date(*parts)
            except (TypeError, ValueError):
                messages.error(request, 'تاریخ عضویت نامعتبر است')
                return redirect('students:student_edit', pk=pk)

        with transaction.atomic():
            user.first_name = first_name
            user.last_name = last_name
            user.national_code = request.POST.get('national_code', '').strip() or None

            student.address = request.POST.get('address', '').strip()
            student.birth_date = birth_date
            student.sport_id = request.POST.get('sport') or None
            student.current_belt = request.POST.get('current_belt', student.current_belt)
            student.joined_at = joined_at
            student.notes = request.POST.get('notes', '').strip()

            for club_id in add_ids:
                StudentClub.objects.get_or_create(
                    student=student,
                    club_id=club_id,
                    defaults={'is_active': True, 'joined_at': jdatetime.date.today()},
                )
                StudentClub.objects.filter(
                    student=student, club_id=club_id, is_active=False
                ).update(is_active=True)

            if deactivate_ids:
                StudentClub.objects.filter(
                    student=student, pk__in=deactivate_ids, is_active=True
                ).update(is_active=False)

            active_membership = student.club_memberships.filter(
                is_active=True
            ).order_by('joined_at', 'pk').first()
            if active_membership and (
                student.club_id != active_membership.club_id
                or student.club_memberships.filter(
                    club_id=student.club_id, is_active=True
                ).exists() is False
            ):
                student.club = active_membership.club

            if new_shift:
                Enrollment.objects.get_or_create(
                    student=student,
                    shift=new_shift,
                    defaults={'enrolled_at': jdatetime.date.today()},
                )

            if request.user.is_super_manager:
                user.is_instructor = request.POST.get('is_instructor') == 'on'
                user.is_club_manager = request.POST.get('is_club_manager') == 'on'

            user.save()
            student.save()

        messages.success(request, 'اطلاعات و عضویت‌های هنرجو با موفقیت بروزرسانی شد')
        return redirect('students:student_detail', pk=pk)


class StudentCreateView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'students/student_add.html'
    form_class = StudentCreateForm
    success_url = reverse_lazy('students:student_list')
    
    def test_func(self):
        user = self.request.user
        return user.is_super_manager or user.is_club_manager

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        student = form.save()
        messages.success(self.request, f'{student.user.get_full_name()} با موفقیت ثبت شد')
        # مستقیم بره صفحه ویرایش
        return redirect('students:student_detail', pk=student.pk)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = jdatetime.date.today()
        return context


class StudentDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return can_manage_students(self.request.user)

    def post(self, request, pk):
        student = get_object_or_404(managed_students_for(request.user), pk=pk)
        user = student.user
        name = user.get_full_name()

        # حذف دائمی فقط برای رکورد اشتباه و فاقد سابقه عملیاتی مجاز است.
        has_financial_history = (
            student.payments.exists()
            or student.transactions.exists()
            or student.fee_dues.exists()
        )
        has_attendance_history = student.attendances.exists()
        has_messages = user.sent_messages.exists() or user.received_messages.exists()
        has_other_roles = (
            user.is_super_manager or user.is_club_manager or user.is_instructor
        )

        if has_financial_history or has_attendance_history or has_messages or has_other_roles:
            messages.error(
                request,
                'این هنرجو سابقه مالی، حضور و غیاب، پیام یا نقش کاربری دیگری دارد؛ '
                'حذف دائمی مجاز نیست. برای توقف عضویت از گزینه غیرفعال‌سازی استفاده کنید.'
            )
            return redirect('students:student_detail', pk=pk)

        with transaction.atomic():
            # حساب کاربری و شماره همراه حفظ می‌شود؛ کد ملی آزاد می‌شود تا
            # در صورت ثبت مجدد هنرجو، رکورد جدید با همان کد ملی ساخته شود.
            user.national_code = None
            user.save(update_fields=['national_code'])
            student.delete()

        messages.success(request, f'رکورد اشتباه هنرجو «{name}» حذف شد')
        return redirect('students:student_list')


class StudentDeactivateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return can_manage_students(self.request.user)

    def post(self, request, pk):
        student = get_object_or_404(managed_students_for(request.user), pk=pk)
        if student.is_active:
            student.is_active = False
            student.save(update_fields=['is_active'])
            messages.success(request, f'عضویت {student.user.get_full_name()} غیرفعال شد')
        else:
            messages.info(request, 'این هنرجو قبلاً غیرفعال شده است')
        return redirect('students:student_detail', pk=pk)


class StudentAvatarView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not can_manage_students(request.user):
            messages.error(request, 'دسترسی غیرمجاز')
            return redirect('students:student_detail', pk=pk)
        
        student = get_object_or_404(managed_students_for(request.user), pk=pk)
        avatar = request.FILES.get('avatar')
        if avatar:
            student.user.avatar = avatar
            student.user.save()
            messages.success(request, 'تصویر پروفایل بروزرسانی شد')
        return redirect('students:student_detail', pk=pk)


class ContactDeleteView(LoginRequiredMixin, View):
    def post(self, request, contact_pk):
        try:
            contact = get_object_or_404(StudentContact, pk=contact_pk, student__in=managed_students_for(request.user))
            student_pk = contact.student.pk
            contact.delete()
            messages.success(request, 'شماره تماس حذف شد')
        except Exception as e:
            messages.error(request, f'خطا در حذف شماره: {str(e)}')
            student_pk = request.POST.get('student_pk', 0)
        
        return redirect('students:student_detail', pk=student_pk)


class InsuranceCreateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        student = get_object_or_404(managed_students_for(request.user), pk=pk)
        
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
        student = get_object_or_404(managed_students_for(request.user), pk=pk)
        
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
        return can_manage_attendance(self.request.user)
    
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
        context['shifts'] = visible_shifts_for(self.request.user).filter(is_active=True, class_group__is_active=True).select_related('class_group')
        
        shift_id = self.request.GET.get('shift')
        if shift_id:
            shift = get_object_or_404(visible_shifts_for(self.request.user), pk=shift_id)
            context['selected_shift'] = shift
            
            # فقط هنرجویانی که قبل از تاریخ انتخاب شده ثبت‌نام کردن
            enrollments = Enrollment.objects.filter(
                shift=shift, is_active=True, student__is_active=True,
                enrolled_at__lte=today
            )

            enrollment_list = list(enrollments.select_related('student__user'))
            students = [e.student for e in enrollment_list]

            # محاسبه ماه‌های فاقد پرداخت برای هر هنرجو از زمان ثبت‌نام در همین شیفت
            # پرداخت ثبت‌شده در FeeDue یا Payment هر دو به‌عنوان پرداخت‌شده محسوب می‌شوند.
            student_ids = [student.id for student in students]
            month_ranges = {}
            all_months = set()

            for enrollment in enrollment_list:
                start = enrollment.enrolled_at
                start_index = start.year * 12 + start.month - 1
                end_index = today.year * 12 + today.month - 1
                months = [
                    f'{index // 12}/{index % 12 + 1:02d}'
                    for index in range(start_index, end_index + 1)
                ] if start_index <= end_index else []
                month_ranges[enrollment.student_id] = months
                all_months.update(months)

            paid_pairs = set()
            if student_ids and all_months:
                paid_pairs.update(
                    FeeDue.objects.filter(
                        student_id__in=student_ids,
                        month__in=all_months,
                        is_paid=True,
                    ).values_list('student_id', 'month')
                )
                paid_pairs.update(
                    Payment.objects.filter(
                        student_id__in=student_ids,
                        month__in=all_months,
                    ).values_list('student_id', 'month')
                )

            for student in students:
                student.unpaid_months = [
                    month for month in month_ranges.get(student.id, [])
                    if (student.id, month) not in paid_pairs
                ]
                student.unpaid_month_count = len(student.unpaid_months)

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


class AttendanceSaveView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return can_manage_attendance(self.request.user)

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
        
        shift = get_object_or_404(visible_shifts_for(request.user), pk=shift_id)
        
        # تاریخ
        if date_str:
            try:
                parts = list(map(int, date_str.replace('/', '-').split('-')))
                date = jdatetime.date(*parts)
            except:
                date = jdatetime.date.today()
        else:
            date = jdatetime.date.today()
        
        enrollments = Enrollment.objects.filter(shift=shift, is_active=True, student__is_active=True, student__in=managed_students_for(request.user))
        
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


class AttendanceToggleView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return can_manage_attendance(self.request.user)

    def post(self, request, student_id):
        student = get_object_or_404(managed_students_for(request.user), pk=student_id)
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
            total = managed_students_for(user).filter(is_active=True).count()
        else:
            total = managed_students_for(user).filter(is_active=True).distinct().count()
        present = Attendance.objects.filter(student__in=managed_students_for(user), date=today, status='present').count()
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
        return managed_students_for(user).filter(is_active=True).select_related('user', 'club').prefetch_related('contacts', 'attendances')
    
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
            all_students = visible_students_for(user).filter(is_active=True).select_related('user')
            all_shifts = visible_shifts_for(user).filter(is_active=True).select_related('class_group')
        elif user.is_club_manager:
            all_students = visible_students_for(user).filter(is_active=True).select_related('user')
            all_shifts = visible_shifts_for(user).filter(is_active=True).select_related('class_group')
        else:
            all_students = visible_students_for(user).filter(is_active=True).select_related('user')
            all_shifts = Shift.objects.none()
        
        context['all_students'] = all_students
        context['all_shifts'] = all_shifts
        
        # فیلترها
        students = all_students
        shift = None
        if shift_id:
            shift = get_object_or_404(all_shifts, pk=shift_id)
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
        contact = get_object_or_404(StudentContact, pk=contact_pk, student__in=managed_students_for(request.user))
        return render(request, 'students/contact_edit.html', {'contact': contact})
    
    def post(self, request, contact_pk):
        contact = get_object_or_404(StudentContact, pk=contact_pk, student__in=managed_students_for(request.user))
        
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


class ClassGroupActivateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return can_manage_students(self.request.user)

    def post(self, request, pk):
        class_group = get_object_or_404(ClassGroup, pk=pk, club__in=managed_clubs_for(request.user))
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
        return ClassGroup.objects.filter(club__in=managed_clubs_for(user), is_active=True).select_related('club', 'sport').distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['inactive_classes'] = ClassGroup.objects.filter(club__in=managed_clubs_for(self.request.user), is_active=False)    
        context['clubs'] = managed_clubs_for(self.request.user).filter(is_active=True)
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
            club = get_object_or_404(managed_clubs_for(request.user), pk=club_id)
            ClassGroup.objects.create(
                name=name, club=club, sport_id=sport_id,
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
        class_group = get_object_or_404(ClassGroup, pk=pk, club__in=managed_clubs_for(request.user))
        class_group.name = request.POST.get('name', class_group.name).strip()
        club_id = request.POST.get('club')
        if club_id:
            class_group.club = get_object_or_404(managed_clubs_for(request.user), pk=club_id)
        class_group.sport_id = request.POST.get('sport', class_group.sport_id)
        class_group.gender = request.POST.get('gender', class_group.gender)
        class_group.description = request.POST.get('description', '')
        class_group.save()
        messages.success(request, 'کلاس بروزرسانی شد')
        return redirect('students:class_list')


class ClassGroupDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        class_group = get_object_or_404(ClassGroup, pk=pk)
        name = class_group.name
        
        # چک کن شیفت فعال داره؟
        if class_group.shifts.filter(is_active=True).exists():
            messages.error(request, f'کلاس "{name}" شیفت فعال دارد. ابتدا شیفت‌ها را غیرفعال کنید.')
        elif class_group.shifts.filter(enrollments__is_active=True).exists():
            messages.error(request, f'کلاس "{name}" هنرجوی ثبت‌نام شده دارد. ابتدا ثبت‌نام‌ها را حذف کنید.')
        else:
            class_group.delete()
            messages.success(request, f'کلاس "{name}" حذف شد')
        
        return redirect('students:class_list')


class ShiftActivateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return can_manage_students(self.request.user)

    def post(self, request, pk):
        shift = get_object_or_404(visible_shifts_for(request.user), pk=pk)
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
        self.class_group = get_object_or_404(ClassGroup, pk=self.kwargs['class_id'], club__in=managed_clubs_for(self.request.user))
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
        class_group = get_object_or_404(ClassGroup, pk=class_id, club__in=managed_clubs_for(request.user))
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
        shift = get_object_or_404(visible_shifts_for(request.user), pk=pk)
        shift.name = request.POST.get('name', shift.name).strip()
        shift.days = request.POST.get('days', shift.days).strip()
        shift.start_time = request.POST.get('start_time') or shift.start_time
        shift.end_time = request.POST.get('end_time') or shift.end_time
        shift.save()
        messages.success(request, 'شیفت بروزرسانی شد')
        return redirect('students:shift_list', class_id=shift.class_group_id)


class ShiftDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        shift = get_object_or_404(Shift, pk=pk)
        name = shift.name
        class_id = shift.class_group_id
        
        # چک کن enrollment فعال داره؟
        if shift.enrollments.filter(is_active=True).exists():
            messages.error(request, f'شیفت "{name}" هنرجوی ثبت‌نام شده دارد. ابتدا ثبت‌نام‌ها را حذف کنید.')
        elif shift.attendances.exists():
            messages.error(request, f'شیفت "{name}" حضور و غیاب ثبت شده دارد. ابتدا حضور و غیاب‌ها را حذف کنید.')
        else:
            shift.delete()
            messages.success(request, f'شیفت "{name}" حذف شد')
        
        return redirect('students:shift_list', class_id=class_id)


class EnrollmentListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'students/enrollment_list.html'
    context_object_name = 'enrollments'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_super_manager or self.request.user.is_club_manager
    
    def get_queryset(self):
        return Enrollment.objects.filter(student__in=managed_students_for(self.request.user), student__is_active=True, is_active=True).select_related(
            'student__user', 'student__club', 'shift__class_group__sport', 'shift__class_group__club'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['students'] = managed_students_for(self.request.user).filter(is_active=True).select_related('user', 'club')
        context['shifts'] = visible_shifts_for(self.request.user).filter(is_active=True, class_group__is_active=True).select_related('class_group')
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
            student = get_object_or_404(managed_students_for(request.user), pk=student_id)
            shift = get_object_or_404(visible_shifts_for(request.user), pk=shift_id)

            if not StudentClub.objects.filter(
                student=student,
                club=shift.class_group.club,
                is_active=True,
            ).exists():
                messages.error(request, 'این هنرجو در باشگاه انتخاب‌شده عضویت فعال ندارد')
                return redirect('students:enrollment_list')

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


class EnrollmentEditView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return can_manage_students(self.request.user)

    def post(self, request, pk):
        enrollment = get_object_or_404(Enrollment, pk=pk, student__in=managed_students_for(request.user))
        shift_id = request.POST.get('shift')
        monthly_fee = request.POST.get('monthly_fee', '0').replace(',', '')
        enrolled_at_str = request.POST.get('enrolled_at', '')
        
        if shift_id:
            if str(enrollment.shift_id) != str(shift_id):
                target_shift = get_object_or_404(visible_shifts_for(request.user), pk=shift_id)
                if not StudentClub.objects.filter(
                    student=enrollment.student,
                    club=target_shift.class_group.club,
                    is_active=True,
                ).exists():
                    messages.error(request, 'این هنرجو در باشگاه شیفت انتخاب‌شده عضویت فعال ندارد')
                    return redirect('students:enrollment_list')
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
        enrollment = get_object_or_404(
            Enrollment,
            pk=pk,
            student__in=managed_students_for(request.user),
            shift__in=visible_shifts_for(request.user),
        )
        name = enrollment.student.user.get_full_name()
        shift_name = enrollment.shift.name

        if enrollment.is_active:
            enrollment.is_active = False
            enrollment.save(update_fields=['is_active'])
            messages.success(
                request,
                f'ثبت‌نام {name} در شیفت «{shift_name}» لغو شد؛ سوابق حضور و غیاب حفظ شدند.'
            )
        else:
            messages.info(request, 'این ثبت‌نام قبلاً لغو شده است')
        return redirect('students:enrollment_list')

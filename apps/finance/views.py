from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Sum

import jdatetime
from .models import Payment, Expense, FeeDue
from apps.students.models import Student
from apps.clubs.models import Club
from apps.finance.models import Payment


def managed_clubs_for(user):
    if user.is_super_manager:
        return Club.objects.all()
    if user.is_club_manager:
        return Club.objects.filter(memberships__user=user, memberships__is_active=True).distinct()
    return Club.objects.none()


def managed_students_for(user):
    if user.is_super_manager:
        return Student.objects.all()
    if user.is_club_manager:
        return Student.objects.filter(club__in=managed_clubs_for(user)).distinct()
    return Student.objects.none()


def visible_payments_for(user):
    if user.is_super_manager:
        return Payment.objects.all()
    if user.is_club_manager:
        return Payment.objects.filter(student__club__in=managed_clubs_for(user)).distinct()
    try:
        return Payment.objects.filter(student=user.student_profile)
    except Student.DoesNotExist:
        return Payment.objects.none()


def managed_expenses_for(user):
    if user.is_super_manager:
        return Expense.objects.all()
    if user.is_club_manager:
        return Expense.objects.filter(club__in=managed_clubs_for(user)).distinct()
    return Expense.objects.none()


def can_manage_finance(user):
    return user.is_super_manager or user.is_club_manager


class PaymentListView(LoginRequiredMixin, ListView):
    template_name = 'finance/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 20
    
    def get_queryset(self):
        return visible_payments_for(self.request.user).select_related('student__user', 'student__club')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['students'] = managed_students_for(self.request.user).filter(is_active=True).select_related('user', 'club')
        return context


class PaymentCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return can_manage_finance(self.request.user)

    def get(self, request):
        students = managed_students_for(request.user).filter(is_active=True).select_related('user', 'club')
        return render(request, 'finance/payment_add.html', {'students': students})
    
    def post(self, request):
        student_id = request.POST.get('student')
        amount_str = request.POST.get('amount', '0').replace(',', '')
        payment_date_str = request.POST.get('payment_date')
        month = request.POST.get('month', '')
        method = request.POST.get('method', 'cash')
        description = request.POST.get('description', '')
        
        # خطاها رو جمع کن
        errors = []
        if not student_id:
            errors.append('هنرجو را انتخاب کنید')
        if not amount_str:
            errors.append('مبلغ را وارد کنید')
        if not payment_date_str:
            errors.append('تاریخ را وارد کنید')
        if not month:
            errors.append('ماه را وارد کنید')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('finance:payment_add')
        
        try:
            amount = int(float(amount_str))
            parts = list(map(int, payment_date_str.replace('/', '-').split('-')))
            date = jdatetime.date(*parts)
            student = get_object_or_404(managed_students_for(request.user), pk=student_id)
            
            Payment.objects.create(
                student=student,
                amount=amount,
                payment_date=date,
                month=month,
                method=method,
                description=description
            )
            messages.success(request, 'پرداخت با موفقیت ثبت شد')
            return redirect('finance:payment_list')
        except Exception as e:
            messages.error(request, f'خطا در ثبت: {e}')
            return redirect('finance:payment_add')


class PaymentEditView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return can_manage_finance(self.request.user)

    def get(self, request, pk):
        payment = get_object_or_404(visible_payments_for(request.user).select_related('student__user', 'student__club'), pk=pk)
        return render(request, 'finance/payment_edit.html', {'payment': payment})
    
    def post(self, request, pk):
        payment = get_object_or_404(visible_payments_for(request.user), pk=pk)
        payment.amount = int(request.POST.get('amount', '0').replace(',', ''))
        date_str = request.POST.get('payment_date')
        if date_str:
            parts = list(map(int, date_str.replace('/', '-').split('-')))
            payment.payment_date = jdatetime.date(*parts)
        payment.month = request.POST.get('month', payment.month)
        payment.method = request.POST.get('method', payment.method)
        payment.save()
        messages.success(request, 'پرداخت بروزرسانی شد')
        return redirect('finance:payment_list')


class PaymentDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return can_manage_finance(self.request.user)

    def post(self, request, pk):
        payment = get_object_or_404(visible_payments_for(request.user), pk=pk)
        payment.delete()
        messages.success(request, 'پرداخت حذف شد')
        return redirect('finance:payment_list')


class ExpenseListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'finance/expense_list.html'
    context_object_name = 'expenses'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_super_manager or self.request.user.is_club_manager
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_manager:
            return Expense.objects.select_related('club')
        return managed_expenses_for(user).select_related('club')


class ExpenseCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return self.request.user.is_super_manager or self.request.user.is_club_manager
    
    def get(self, request):
        clubs = managed_clubs_for(request.user).filter(is_active=True)
        return render(request, 'finance/expense_add.html', {'clubs': clubs})
    
    def post(self, request):
        club_id = request.POST.get('club')
        title = request.POST.get('title', '')
        amount = request.POST.get('amount', '0').replace(',', '')
        expense_date = request.POST.get('expense_date')
        category = request.POST.get('category', 'other')
        description = request.POST.get('description', '')
        
        if club_id and title and amount and expense_date:
            try:
                parts = list(map(int, expense_date.replace('/', '-').split('-')))
                club = get_object_or_404(managed_clubs_for(request.user).filter(is_active=True), pk=club_id)
                Expense.objects.create(
                    club=club,
                    title=title,
                    amount=int(float(amount)),
                    expense_date=jdatetime.date(*parts),
                    category=category,
                    description=description
                )
                messages.success(request, 'هزینه ثبت شد')
                return redirect('finance:expense_list')
            except Exception as e:
                messages.error(request, str(e))
        else:
            messages.error(request, 'همه فیلدهای ستاره‌دار الزامی است')
        return redirect('finance:expense_add')


class ExpenseEditView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return self.request.user.is_super_manager or self.request.user.is_club_manager
    
    def get(self, request, pk):
        expense = get_object_or_404(managed_expenses_for(request.user), pk=pk)
        clubs = managed_clubs_for(request.user).filter(is_active=True)
        return render(request, 'finance/expense_edit.html', {'expense': expense, 'clubs': clubs})
    
    def post(self, request, pk):
        expense = get_object_or_404(managed_expenses_for(request.user), pk=pk)
        club_id = request.POST.get('club')
        if club_id:
            expense.club = get_object_or_404(managed_clubs_for(request.user), pk=club_id)
        expense.title = request.POST.get('title', expense.title)
        expense.amount = int(request.POST.get('amount', '0').replace(',', ''))
        date_str = request.POST.get('expense_date')
        if date_str:
            parts = list(map(int, date_str.replace('/', '-').split('-')))
            expense.expense_date = jdatetime.date(*parts)
        expense.category = request.POST.get('category', expense.category)
        expense.description = request.POST.get('description', '')
        expense.save()
        messages.success(request, 'هزینه بروزرسانی شد')
        return redirect('finance:expense_list')


class ExpenseDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self): return can_manage_finance(self.request.user)

    def post(self, request, pk):
        expense = get_object_or_404(managed_expenses_for(request.user), pk=pk)
        expense.delete()
        messages.success(request, 'هزینه حذف شد')
        return redirect('finance:expense_list')


class ReportView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'finance/report.html'
    
    def test_func(self):
        return self.request.user.is_super_manager or self.request.user.is_club_manager
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.is_super_manager:
            total_income = Payment.objects.aggregate(s=Sum('amount'))['s'] or 0
            total_expense = Expense.objects.aggregate(s=Sum('amount'))['s'] or 0
        else:
            total_income = visible_payments_for(user).aggregate(s=Sum('amount'))['s'] or 0
            total_expense = managed_expenses_for(user).aggregate(s=Sum('amount'))['s'] or 0
        
        context['total_income'] = total_income
        context['total_expense'] = total_expense
        context['balance'] = total_income - total_expense
        return context


class FeeAddView(LoginRequiredMixin, View):
    def post(self, request, student_pk):
        student = get_object_or_404(Student, pk=student_pk)
        month = request.POST.get('month')
        amount = request.POST.get('amount')
        paid_at_str = request.POST.get('paid_at')

        paid_at = None
        if paid_at_str:
            try:
                parts = list(map(int, paid_at_str.replace('/', '-').split('-')))
                paid_at = jdatetime.date(*parts)
            except:
                pass

        FeeDue.objects.update_or_create(
            student=student,
            month=month,
            defaults={
                'amount': int(amount) if amount else 0,
                'is_paid': True,
                'paid_at': paid_at or jdatetime.date.today()
            }
        )

        Payment.objects.create(
            student=student,
            amount=int(amount) if amount else 0,
            payment_date=paid_at or jdatetime.date.today(),
            month=month,
            method='cash',
            description=f'شهریه {month}'
        )

        messages.success(request, f'شهریه {month} ثبت شد')
        return redirect('students:student_detail', pk=student.pk)

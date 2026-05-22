from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Sum
import jdatetime
from .models import Payment, Expense
from apps.students.models import Student
from apps.clubs.models import Club


class PaymentListView(LoginRequiredMixin, ListView):
    template_name = 'finance/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_manager:
            qs = Payment.objects.select_related('student__user', 'student__club')
        elif user.is_club_manager:
            clubs = Club.objects.filter(memberships__user=user, is_active=True)
            qs = Payment.objects.filter(student__club__in=clubs).select_related('student__user', 'student__club')
        else:
            try:
                student = user.student_profile
                qs = Payment.objects.filter(student=student).select_related('student__club')
            except:
                qs = Payment.objects.none()
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['students'] = Student.objects.filter(is_active=True).select_related('user', 'club')
        return context


class PaymentCreateView(LoginRequiredMixin, View):
    def get(self, request):
        students = Student.objects.filter(is_active=True).select_related('user', 'club')
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
            
            Payment.objects.create(
                student_id=student_id,
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


class PaymentEditView(LoginRequiredMixin, View):
    def get(self, request, pk):
        payment = get_object_or_404(Payment.objects.select_related('student__user', 'student__club'), pk=pk)
        return render(request, 'finance/payment_edit.html', {'payment': payment})
    
    def post(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk)
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


class PaymentDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk)
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
        clubs = Club.objects.filter(memberships__user=user, is_active=True)
        return Expense.objects.filter(club__in=clubs).select_related('club')


class ExpenseCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_super_manager or self.request.user.is_club_manager
    
    def get(self, request):
        clubs = Club.objects.filter(is_active=True)
        return render(request, 'finance/expense_add.html', {'clubs': clubs})
    
    def post(self, request):
        club_id = request.POST.get('club')
        title = request.POST.get('title', '')
        amount = request.POST.get('amount', '').replace(',', '')
        expense_date = request.POST.get('expense_date')
        category = request.POST.get('category', 'other')
        description = request.POST.get('description', '')
        
        if club_id and title and amount and expense_date:
            try:
                parts = list(map(int, expense_date.replace('/', '-').split('-')))
                date = jdatetime.date(*parts)
                Expense.objects.create(
                    club_id=club_id,
                    title=title,
                    amount=int(amount),
                    expense_date=date,
                    category=category,
                    description=description
                )
                messages.success(request, 'هزینه با موفقیت ثبت شد')
                return redirect('finance:expense_list')
            except:
                messages.error(request, 'تاریخ نامعتبر است')
        else:
            messages.error(request, 'همه فیلدهای ستاره‌دار الزامی است')
        
        return redirect('finance:expense_add')


class ExpenseEditView(LoginRequiredMixin, View):
    def post(self, request, pk):
        expense = get_object_or_404(Expense, pk=pk)
        expense.title = request.POST.get('title', expense.title)
        expense.amount = int(request.POST.get('amount', expense.amount).replace(',', ''))
        expense.expense_date = jdatetime.date(*map(int, request.POST.get('expense_date').split('/')))
        expense.category = request.POST.get('category', expense.category)
        expense.description = request.POST.get('description', expense.description)
        expense.save()
        messages.success(request, 'هزینه بروزرسانی شد')
        return redirect('finance:expense_list')


class ExpenseDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        expense = get_object_or_404(Expense, pk=pk)
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
            clubs = Club.objects.filter(memberships__user=user, is_active=True)
            total_income = Payment.objects.filter(club__in=clubs).aggregate(s=Sum('amount'))['s'] or 0
            total_expense = Expense.objects.filter(club__in=clubs).aggregate(s=Sum('amount'))['s'] or 0
        
        context['total_income'] = total_income
        context['total_expense'] = total_expense
        context['balance'] = total_income - total_expense
        return context

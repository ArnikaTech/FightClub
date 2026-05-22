from django.contrib import admin
from .models import Payment, Expense

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['student', 'amount', 'payment_date', 'month', 'method']
    list_filter = [ 'method', 'payment_date']
    search_fields = ['student__user__first_name', 'student__user__last_name']
    autocomplete_fields = ['student']

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['title', 'club', 'amount', 'expense_date', 'category']
    list_filter = ['club', 'category', 'expense_date']
    search_fields = ['title']
    autocomplete_fields = ['club']

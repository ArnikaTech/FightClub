from django.test import TestCase
from django.urls import reverse

import jdatetime

from apps.accounts.models import User
from apps.clubs.models import City, Club, ClubMembership, Organization, Province
from apps.students.models import Student
from .models import Expense, FeeDue, Payment


class FinanceTenantAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        province = Province.objects.create(name='استان آزمایشی')
        city = City.objects.create(name='شهر آزمایشی', province=province)

        cls.organization_a = Organization.objects.create(
            name='مجموعه الف', slug='org-a'
        )
        cls.organization_b = Organization.objects.create(
            name='مجموعه ب', slug='org-b'
        )
        cls.club_a = Club.objects.create(
            organization=cls.organization_a,
            name='شعبه الف',
            province=province,
            city=city,
        )
        cls.club_b = Club.objects.create(
            organization=cls.organization_b,
            name='شعبه ب',
            province=province,
            city=city,
        )

        cls.manager_a = User.objects.create_user(
            phone='09120000001',
            password='test-password',
            first_name='مدیر',
            last_name='الف',
            is_club_manager=True,
        )
        cls.manager_b = User.objects.create_user(
            phone='09120000002',
            password='test-password',
            first_name='مدیر',
            last_name='ب',
            is_club_manager=True,
        )
        ClubMembership.objects.create(user=cls.manager_a, club=cls.club_a, role='manager')
        ClubMembership.objects.create(user=cls.manager_b, club=cls.club_b, role='manager')

        student_user = User.objects.create_user(
            phone='09120000003',
            password='test-password',
            first_name='هنرجوی',
            last_name='الف',
        )
        cls.student = Student.objects.create(\n            user=student_user, club=cls.club_a, student_code='TEST-001'\n        )
        cls.other_student_user = User.objects.create_user(
            phone='09120000004',
            password='test-password',
            first_name='هنرجوی',
            last_name='ب',
        )
        cls.other_student = Student.objects.create(
            user=cls.other_student_user, club=cls.club_b, student_code='TEST-002'
        )

        cls.payment = Payment.objects.create(
            student=cls.other_student,
            amount=100000,
            payment_date=jdatetime.date(1405, 1, 10),
            month='1405/01',
        )
        cls.expense = Expense.objects.create(
            club=cls.club_b,
            title='هزینه شعبه ب',
            amount=50000,
            expense_date=jdatetime.date(1405, 1, 10),
        )
        cls.fee_due = FeeDue.objects.create(
            student=cls.other_student,
            month='1405/01',
            amount=100000,
            is_paid=False,
        )

    def test_manager_cannot_open_payment_from_another_organization(self):
        self.client.force_login(self.manager_a)

        response = self.client.get(
            reverse('finance:payment_edit', args=[self.payment.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_manager_cannot_delete_payment_from_another_organization(self):
        self.client.force_login(self.manager_a)

        response = self.client.post(
            reverse('finance:payment_delete', args=[self.payment.pk])
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Payment.objects.filter(pk=self.payment.pk).exists())

    def test_manager_cannot_open_expense_from_another_organization(self):
        self.client.force_login(self.manager_a)

        response = self.client.get(
            reverse('finance:expense_edit', args=[self.expense.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_manager_cannot_delete_expense_from_another_organization(self):
        self.client.force_login(self.manager_a)

        response = self.client.post(
            reverse('finance:expense_delete', args=[self.expense.pk])
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Expense.objects.filter(pk=self.expense.pk).exists())

    def test_manager_cannot_edit_fee_due_for_another_organization(self):
        self.client.force_login(self.manager_a)

        response = self.client.post(
            reverse('finance:fee_edit', args=[self.fee_due.pk]),
            {'amount': '200000', 'month': '1405/02'},
        )

        self.assertEqual(response.status_code, 404)
        self.fee_due.refresh_from_db()
        self.assertEqual(self.fee_due.amount, 100000)

    def test_manager_cannot_delete_fee_due_for_another_organization(self):
        self.client.force_login(self.manager_a)

        response = self.client.post(
            reverse('finance:fee_delete', args=[self.fee_due.pk])
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(FeeDue.objects.filter(pk=self.fee_due.pk).exists())

    def test_manager_cannot_add_fee_for_student_from_another_organization(self):
        self.client.force_login(self.manager_a)
        payment_count = Payment.objects.count()

        response = self.client.post(
            reverse('finance:fee_add', args=[self.other_student.pk]),
            {'month': '1405/02', 'amount': '100000'},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Payment.objects.count(), payment_count)
        self.assertFalse(
            FeeDue.objects.filter(student=self.other_student, month='1405/02').exists()
        )

    def test_manager_can_access_payment_in_their_own_organization(self):
        own_payment = Payment.objects.create(
            student=self.student,
            amount=75000,
            payment_date=jdatetime.date(1405, 1, 11),
            month='1405/01',
        )
        self.client.force_login(self.manager_a)

        response = self.client.get(
            reverse('finance:payment_edit', args=[own_payment.pk])
        )

        self.assertEqual(response.status_code, 200)

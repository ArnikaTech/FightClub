from datetime import time

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.clubs.models import (
    City,
    Club,
    ClubMembership,
    Organization,
    Province,
    Sport,
)
from apps.students.models import ClassGroup, Shift, Student, StudentClub


class DashboardOverviewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        province = Province.objects.create(name="استان آزمایش")
        city = City.objects.create(name="شهر آزمایش", province=province)
        sport = Sport.objects.create(name="رشته آزمایش")

        organization_a = Organization.objects.create(
            name="مجموعه الف",
            slug="organization-a",
        )
        organization_b = Organization.objects.create(
            name="مجموعه ب",
            slug="organization-b",
        )

        cls.club_a = Club.objects.create(
            organization=organization_a,
            name="شعبه الف",
            province=province,
            city=city,
        )
        cls.club_b = Club.objects.create(
            organization=organization_a,
            name="شعبه ب",
            province=province,
            city=city,
        )
        cls.club_c = Club.objects.create(
            organization=organization_b,
            name="شعبه ج",
            province=province,
            city=city,
        )

        cls.manager_a = User.objects.create_user(
            phone="09120000001",
            password="test-pass",
            first_name="مدیر",
            last_name="الف",
            is_club_manager=True,
        )
        cls.manager_b = User.objects.create_user(
            phone="09120000002",
            password="test-pass",
            first_name="مدیر",
            last_name="ب",
            is_club_manager=True,
        )
        cls.super_manager = User.objects.create_user(
            phone="09120000003",
            password="test-pass",
            first_name="مدیر",
            last_name="کل",
            is_super_manager=True,
        )

        ClubMembership.objects.create(
            user=cls.manager_a,
            club=cls.club_a,
            role="manager",
        )
        ClubMembership.objects.create(
            user=cls.manager_a,
            club=cls.club_b,
            role="manager",
        )
        ClubMembership.objects.create(
            user=cls.manager_b,
            club=cls.club_c,
            role="manager",
        )

        cls.student_a = cls._create_student(
            "09121110001", "OV-001", cls.club_a, True
        )
        cls.student_b = cls._create_student(
            "09121110002", "OV-002", cls.club_b, True
        )
        cls.student_inactive = cls._create_student(
            "09121110003", "OV-003", cls.club_a, False
        )
        cls.student_other_tenant = cls._create_student(
            "09121110004", "OV-004", cls.club_c, True
        )
        cls.student_inactive_membership = cls._create_student(
            "09121110005", "OV-005", cls.club_c, True
        )

        # هنرجوی اول در هر دو شعبه عضویت دارد، اما باید فقط یک بار شمرده شود.
        StudentClub.objects.create(student=cls.student_a, club=cls.club_b)
        # عضویت غیرفعال در شعبه دیگر نباید باعث ورود هنرجو به آمار آن شعبه شود.
        StudentClub.objects.create(
            student=cls.student_inactive_membership,
            club=cls.club_a,
            is_active=False,
        )

        class_a = ClassGroup.objects.create(
            club=cls.club_a,
            sport=sport,
            name="کلاس الف",
            is_active=True,
        )
        class_b = ClassGroup.objects.create(
            club=cls.club_b,
            sport=sport,
            name="کلاس ب",
            is_active=True,
        )
        inactive_class = ClassGroup.objects.create(
            club=cls.club_b,
            sport=sport,
            name="کلاس غیرفعال",
            is_active=False,
        )
        class_c = ClassGroup.objects.create(
            club=cls.club_c,
            sport=sport,
            name="کلاس ج",
            is_active=True,
        )

        cls._create_shift(class_a, "شیفت الف")
        cls._create_shift(class_b, "شیفت ب")
        cls._create_shift(inactive_class, "شیفت کلاس غیرفعال")
        cls._create_shift(class_c, "شیفت ج")

    @classmethod
    def _create_student(cls, phone, student_code, club, is_active):
        user = User.objects.create_user(
            phone=phone,
            password="test-pass",
            first_name="هنرجو",
            last_name=student_code,
        )
        return Student.objects.create(
            user=user,
            club=club,
            student_code=student_code,
            is_active=is_active,
        )

    @staticmethod
    def _create_shift(class_group, name):
        return Shift.objects.create(
            class_group=class_group,
            name=name,
            days="saturday",
            start_time=time(8, 0),
            end_time=time(9, 0),
            is_active=True,
        )

    def test_manager_sees_only_assigned_branches_and_unique_students(self):
        self.client.force_login(self.manager_a)
        response = self.client.get(reverse("accounts:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["overview_stats"],
            {
                "branches": 2,
                "students_total": 3,
                "students_active": 2,
                "students_inactive": 1,
                "classes": 2,
                "shifts": 2,
            },
        )
        self.assertContains(response, "نمای کلی مجموعه")

    def test_manager_cannot_see_another_tenant_statistics(self):
        self.client.force_login(self.manager_b)
        response = self.client.get(reverse("accounts:dashboard"))

        self.assertEqual(
            response.context["overview_stats"],
            {
                "branches": 1,
                "students_total": 2,
                "students_active": 2,
                "students_inactive": 0,
                "classes": 1,
                "shifts": 1,
            },
        )

    def test_super_manager_can_filter_overview_by_selected_branch(self):
        self.client.force_login(self.super_manager)
        response = self.client.get(
            reverse("accounts:dashboard"),
            {"club_id": self.club_a.pk},
        )

        self.assertEqual(
            response.context["overview_stats"],
            {
                "branches": 1,
                "students_total": 2,
                "students_active": 1,
                "students_inactive": 1,
                "classes": 1,
                "shifts": 1,
                "income": 0,
                "expenses": 0,
            },
        )

    def test_super_manager_sees_all_tenants_without_branch_filter(self):
        self.client.force_login(self.super_manager)
        response = self.client.get(reverse("accounts:dashboard"))

        self.assertEqual(
            response.context["overview_stats"],
            {
                "branches": 3,
                "students_total": 5,
                "students_active": 4,
                "students_inactive": 1,
                "classes": 3,
                "shifts": 3,
                "income": 0,
                "expenses": 0,
            },
        )

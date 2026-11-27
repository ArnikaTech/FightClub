from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.clubs.models import City, Club, Province
from apps.accounts.views import managed_clubs_for as accounts_managed_clubs_for
from apps.students.views import managed_clubs_for as students_managed_clubs_for
from apps.finance.views import managed_clubs_for as finance_managed_clubs_for
from .models import Organization, OrganizationMembership


class OrganizationMembershipTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone="09120000001",
            password="test-pass",
            first_name="مدیر",
            last_name="آزمایش",
        )
        self.organization_a = Organization.objects.create(
            name="مجموعه الف",
            slug="organization-a",
        )
        self.organization_b = Organization.objects.create(
            name="مجموعه ب",
            slug="organization-b",
        )

    def test_user_can_be_member_of_multiple_organizations(self):
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.organization_a,
        )
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.organization_b,
        )

        self.assertEqual(self.user.organization_memberships.count(), 2)
        self.assertSetEqual(
            set(self.user.organization_memberships.values_list("organization_id", flat=True)),
            {self.organization_a.pk, self.organization_b.pk},
        )

    def test_user_can_have_only_one_membership_per_organization(self):
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.organization_a,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OrganizationMembership.objects.create(
                    user=self.user,
                    organization=self.organization_a,
                )

    def test_organization_manager_sees_all_and_only_own_organization_branches(self):
        self.user.is_club_manager = True
        self.user.save(update_fields=["is_club_manager"])
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.organization_a,
            role="manager",
        )

        province = Province.objects.create(name="آزمایش")
        city = City.objects.create(name="شهر آزمایش", province=province)
        own_branch_1 = Club.objects.create(
            organization=self.organization_a,
            name="شعبه اول",
            province=province,
            city=city,
        )
        own_branch_2 = Club.objects.create(
            organization=self.organization_a,
            name="شعبه دوم",
            province=province,
            city=city,
        )
        foreign_branch = Club.objects.create(
            organization=self.organization_b,
            name="شعبه مجموعه دیگر",
            province=province,
            city=city,
        )

        expected = {own_branch_1.pk, own_branch_2.pk}
        for managed_clubs in (
            accounts_managed_clubs_for,
            students_managed_clubs_for,
            finance_managed_clubs_for,
        ):
            self.assertSetEqual(
                set(managed_clubs(self.user).values_list("pk", flat=True)),
                expected,
            )
        self.assertNotIn(foreign_branch.pk, expected)

    def test_platform_owner_can_select_organization_and_dashboard_uses_it(self):
        province = Province.objects.create(name="آزمایش")
        city = City.objects.create(name="شهر آزمایش", province=province)
        Club.objects.create(
            organization=self.organization_a,
            name="شعبه مجموعه الف",
            province=province,
            city=city,
        )
        Club.objects.create(
            organization=self.organization_b,
            name="شعبه مجموعه ب",
            province=province,
            city=city,
        )
        self.user.is_super_manager = True
        self.user.save(update_fields=["is_super_manager"])
        self.client.force_login(self.user)

        selection = self.client.get(
            reverse("accounts:dashboard"),
            {"organization_id": self.organization_a.pk},
        )
        self.assertEqual(selection.status_code, 302)
        response = self.client.get(reverse("accounts:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["overview_stats"]["branches"], 1)
        self.assertEqual(response.context["active_organization"].pk, self.organization_a.pk)

    def test_platform_owner_organization_filter_limits_branches(self):
        province = Province.objects.create(name="آزمایش")
        city = City.objects.create(name="شهر آزمایش", province=province)
        own_branch = Club.objects.create(
            organization=self.organization_a,
            name="شعبه مجموعه الف",
            province=province,
            city=city,
        )
        foreign_branch = Club.objects.create(
            organization=self.organization_b,
            name="شعبه مجموعه ب",
            province=province,
            city=city,
        )
        self.user.is_super_manager = True
        self.user.active_organization_id = self.organization_a.pk

        self.assertSetEqual(
            set(accounts_managed_clubs_for(self.user).values_list("pk", flat=True)),
            {own_branch.pk},
        )
        self.assertNotIn(foreign_branch.pk, set(accounts_managed_clubs_for(self.user).values_list("pk", flat=True)))

    def test_branch_manager_is_scoped_to_assigned_branch(self):
        self.user.is_club_manager = True
        self.user.save(update_fields=["is_club_manager"])
        province = Province.objects.create(name="آزمایش")
        city = City.objects.create(name="شهر آزمایش", province=province)
        branch_a = Club.objects.create(
            organization=self.organization_a,
            name="شعبه مجاز",
            province=province,
            city=city,
        )
        branch_b = Club.objects.create(
            organization=self.organization_a,
            name="شعبه غیرمجاز",
            province=province,
            city=city,
        )
        ClubMembership.objects.create(user=self.user, club=branch_a, role="manager")

        for managed_clubs in (
            accounts_managed_clubs_for,
            students_managed_clubs_for,
            finance_managed_clubs_for,
        ):
            self.assertSetEqual(
                set(managed_clubs(self.user).values_list("pk", flat=True)),
                {branch_a.pk},
            )
        self.assertNotIn(branch_b.pk, set(finance_managed_clubs_for(self.user).values_list("pk", flat=True)))

    def test_multiple_managers_can_belong_to_the_same_organization(self):
        second_manager = User.objects.create_user(
            phone="09120000002",
            password="test-pass",
            first_name="مدیر دوم",
            last_name="آزمایش",
        )
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.organization_a,
            role="manager",
        )
        OrganizationMembership.objects.create(
            user=second_manager,
            organization=self.organization_a,
            role="manager",
        )
        self.assertEqual(
            self.organization_a.memberships.filter(is_active=True, role="manager").count(),
            2,
        )

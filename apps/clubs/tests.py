from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.clubs.models import City, Club, ClubMembership, Province
from apps.accounts.views import managed_clubs_for as accounts_managed_clubs_for
from apps.students.views import managed_clubs_for as students_managed_clubs_for
from apps.finance.views import managed_clubs_for as finance_managed_clubs_for
from apps.students.models import Student
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

    def test_platform_owner_cannot_delete_branch_outside_selected_organization(self):
        province = Province.objects.create(name="آزمایش")
        city = City.objects.create(name="شهر آزمایش", province=province)
        foreign_branch = Club.objects.create(
            organization=self.organization_b,
            name="شعبه مجموعه ب",
            province=province,
            city=city,
        )
        self.user.is_super_manager = True
        self.user.save(update_fields=["is_super_manager"])
        self.client.force_login(self.user)
        self.client.get(
            reverse("accounts:dashboard"),
            {"organization_id": self.organization_a.pk},
        )

        response = self.client.post(reverse("clubs:club_delete", args=[foreign_branch.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Club.objects.filter(pk=foreign_branch.pk).exists())

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

    def test_platform_owner_can_assign_org_manager_without_global_manager_flag(self):
        platform_owner = User.objects.create_user(
            phone="09120000041", password="test-pass", first_name="پشتیبان",
            last_name="پلتفرم", is_super_manager=True,
        )
        manager = User.objects.create_user(
            phone="09120000042", password="test-pass", first_name="مدیر",
            last_name="مجموعه",
        )
        province = Province.objects.create(name="آزمایش")
        city = City.objects.create(name="شهر آزمایش", province=province)
        candidate_branch = Club.objects.create(
            organization=self.organization_a, name="شعبه نامزد", province=province, city=city
        )
        Student.objects.create(user=manager, club=candidate_branch, student_code="orgm-candidate")
        foreign_user = User.objects.create_user(phone="09120000064", password="test-pass")
        foreign_branch = Club.objects.create(
            organization=self.organization_b, name="شعبه مجموعه ب", province=province, city=city
        )
        Student.objects.create(user=foreign_user, club=foreign_branch, student_code="foreign-candidate")
        self.client.force_login(platform_owner)
        detail = self.client.get(reverse("clubs:organization_detail", args=[self.organization_a.pk]))
        self.assertSetEqual(
            set(detail.context["organization_manager_candidates"].values_list("pk", flat=True)),
            {manager.pk},
        )

        response = self.client.post(
            reverse("clubs:organization_manager_add", args=[self.organization_a.pk]),
            {"user_id": manager.pk},
        )

        self.assertEqual(response.status_code, 302)
        membership = OrganizationMembership.objects.get(
            user=manager, organization=self.organization_a
        )
        self.assertTrue(membership.is_active)
        self.assertFalse(manager.is_club_manager)
        detail = self.client.get(reverse("clubs:organization_detail", args=[self.organization_a.pk]))
        self.assertIn(manager, [item.user for item in detail.context["organization_managers"]])

        self.client.force_login(manager)
        self.assertEqual(self.client.get(reverse("clubs:club_list")).status_code, 200)

    def test_revoking_one_membership_preserves_access_to_other_organizations(self):
        platform_owner = User.objects.create_user(
            phone="09120000044", password="test-pass", first_name="پشتیبان",
            last_name="پلتفرم", is_super_manager=True,
        )
        manager = User.objects.create_user(
            phone="09120000045", password="test-pass", first_name="مدیر",
            last_name="مشترک",
        )
        backup_manager = User.objects.create_user(
            phone="09120000046", password="test-pass", first_name="مدیر",
            last_name="پشتیبان",
        )
        membership_a = OrganizationMembership.objects.create(
            user=manager, organization=self.organization_a, role="manager"
        )
        OrganizationMembership.objects.create(
            user=backup_manager, organization=self.organization_a, role="manager"
        )
        OrganizationMembership.objects.create(
            user=manager, organization=self.organization_b, role="manager"
        )
        province = Province.objects.create(name="آزمایش")
        city = City.objects.create(name="شهر آزمایش", province=province)
        branch_b = Club.objects.create(
            organization=self.organization_b, name="شعبه ب", province=province, city=city
        )
        self.client.force_login(platform_owner)

        self.client.post(
            reverse(
                "clubs:organization_manager_deactivate",
                args=[self.organization_a.pk, membership_a.pk],
            )
        )
        manager.active_organization_id = self.organization_b.pk
        self.assertSetEqual(
            set(accounts_managed_clubs_for(manager).values_list("pk", flat=True)),
            {branch_b.pk},
        )

    def test_organization_manager_can_assign_single_branch_manager(self):
        province = Province.objects.create(name="آزمایش")
        city = City.objects.create(name="شهر آزمایش", province=province)
        branch_a = Club.objects.create(organization=self.organization_a, name="الف", province=province, city=city)
        branch_b = Club.objects.create(organization=self.organization_a, name="ب", province=province, city=city)
        branch_foreign = Club.objects.create(organization=self.organization_b, name="ج", province=province, city=city)
        target = User.objects.create_user(phone="09120000061", password="test-pass")
        Student.objects.create(user=target, club=branch_a, student_code="br-a-candidate")
        foreign_target = User.objects.create_user(phone="09120000062", password="test-pass")
        Student.objects.create(user=foreign_target, club=branch_foreign, student_code="branch-b-manager-candidate")
        OrganizationMembership.objects.create(user=self.user, organization=self.organization_a, role="manager")
        self.client.force_login(self.user)
        detail = self.client.get(reverse("clubs:organization_detail", args=[self.organization_a.pk]))
        self.assertSetEqual(
            set(detail.context["branch_manager_candidates"].values_list("pk", flat=True)),
            {target.pk},
        )

        response = self.client.post(
            reverse("clubs:branch_manager_add", args=[self.organization_a.pk, branch_a.pk]),
            {"user_id": target.pk},
        )

        self.assertEqual(response.status_code, 302)
        self.assertSetEqual(
            set(accounts_managed_clubs_for(target).values_list("pk", flat=True)),
            {branch_a.pk},
        )
        response = self.client.post(
            reverse("clubs:branch_manager_add", args=[self.organization_a.pk, branch_foreign.pk]),
            {"user_id": target.pk},
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(accounts_managed_clubs_for(target).filter(pk__in=[branch_b.pk, branch_foreign.pk]).exists())

    def test_can_revoke_last_branch_manager_and_leave_branch_unassigned(self):
        province = Province.objects.create(name="آزمایش")
        city = City.objects.create(name="شهر آزمایش", province=province)
        branch = Club.objects.create(
            organization=self.organization_a, name="شعبه بدون مدیر", province=province, city=city
        )
        manager_user = User.objects.create_user(phone="09120000063", password="test-pass")
        membership = ClubMembership.objects.create(user=manager_user, club=branch, role="manager")
        OrganizationMembership.objects.create(
            user=self.user, organization=self.organization_a, role="manager"
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("clubs:branch_manager_deactivate", args=[self.organization_a.pk, branch.pk, membership.pk])
        )

        self.assertEqual(response.status_code, 302)
        membership.refresh_from_db()
        self.assertFalse(membership.is_active)
        self.assertFalse(accounts_managed_clubs_for(manager_user).filter(pk=branch.pk).exists())

    def test_can_revoke_last_active_organization_manager(self):
        platform_owner = User.objects.create_user(
            phone="09120000043", password="test-pass", first_name="پشتیبان",
            last_name="پلتفرم", is_super_manager=True,
        )
        membership = OrganizationMembership.objects.create(
            user=self.user, organization=self.organization_a, role="manager"
        )
        self.client.force_login(platform_owner)

        response = self.client.post(
            reverse(
                "clubs:organization_manager_deactivate",
                args=[self.organization_a.pk, membership.pk],
            )
        )

        self.assertEqual(response.status_code, 302)
        membership.refresh_from_db()
        self.assertFalse(membership.is_active)

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

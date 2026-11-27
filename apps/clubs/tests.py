from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.accounts.models import User
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

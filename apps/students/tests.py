from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.clubs.models import City, Club, Organization, OrganizationMembership, Province, Sport
from .models import ClassGroup, Shift


class TenantDeleteAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        province = Province.objects.create(name="استان تست")
        city = City.objects.create(name="شهر تست", province=province)
        cls.org_a = Organization.objects.create(name="مجموعه الف", slug="tenant-delete-a")
        cls.org_b = Organization.objects.create(name="مجموعه ب", slug="tenant-delete-b")
        cls.club_a = Club.objects.create(
            organization=cls.org_a, name="باشگاه الف", province=province, city=city
        )
        cls.club_b = Club.objects.create(
            organization=cls.org_b, name="باشگاه ب", province=province, city=city
        )
        sport = Sport.objects.create(name="رشته تست")
        cls.class_a = ClassGroup.objects.create(
            club=cls.club_a, sport=sport, name="کلاس الف"
        )
        cls.class_b = ClassGroup.objects.create(
            club=cls.club_b, sport=sport, name="کلاس ب"
        )
        cls.shift_a = Shift.objects.create(
            class_group=cls.class_a, name="شیفت الف", days="شنبه",
            start_time="09:00", end_time="10:00"
        )
        cls.shift_b = Shift.objects.create(
            class_group=cls.class_b, name="شیفت ب", days="یکشنبه",
            start_time="10:00", end_time="11:00"
        )
        cls.manager = User.objects.create_user(
            phone="09120000031", password="test-password", is_club_manager=True
        )
        OrganizationMembership.objects.create(
            user=cls.manager, organization=cls.org_a, role="manager"
        )
        cls.no_access_user = User.objects.create_user(
            phone="09120000032", password="test-password"
        )

    def test_org_and_branch_manager_memberships_do_not_duplicate_classes(self):
        from apps.clubs.models import ClubMembership
        ClubMembership.objects.create(
            user=self.manager, club=self.club_a, role="manager"
        )
        self.client.force_login(self.manager)

        response = self.client.get(reverse("students:class_list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["classes"].values_list("pk", flat=True)), [self.class_a.pk])

    def test_manager_class_edit_updates_fields_and_preserves_unsubmitted_description(self):
        self.class_a.description = "توضیح موجود"
        self.class_a.save(update_fields=["description"])
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("students:class_edit", args=[self.class_a.pk]),
            {
                "name": "کلاس ویرایش‌شده",
                "club": self.club_a.pk,
                "sport": self.class_a.sport_id,
                "gender": "female",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.class_a.refresh_from_db()
        self.assertEqual(self.class_a.name, "کلاس ویرایش‌شده")
        self.assertEqual(self.class_a.gender, "female")
        self.assertEqual(self.class_a.description, "توضیح موجود")

    def test_manager_enrollment_form_receives_only_permitted_shifts(self):
        self.client.force_login(self.manager)

        response = self.client.get(reverse("students:enrollment_list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.context["shifts"].values_list("pk", flat=True)),
            {self.shift_a.pk},
        )

    def test_platform_owner_class_list_respects_selected_organization(self):
        platform_owner = User.objects.create_user(
            phone="09120000033", password="test-password", is_super_manager=True
        )
        self.client.force_login(platform_owner)
        self.client.get(
            reverse("accounts:dashboard"),
            {"organization_id": self.org_a.pk},
        )

        response = self.client.get(reverse("students:class_list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.context["classes"].values_list("pk", flat=True)),
            {self.class_a.pk},
        )

    def test_manager_cannot_delete_class_from_another_organization(self):
        self.client.force_login(self.manager)
        response = self.client.post(reverse("students:class_delete", args=[self.class_b.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(ClassGroup.objects.filter(pk=self.class_b.pk).exists())

    def test_manager_cannot_delete_shift_from_another_organization(self):
        self.client.force_login(self.manager)
        response = self.client.post(reverse("students:shift_delete", args=[self.shift_b.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Shift.objects.filter(pk=self.shift_b.pk).exists())

    def test_user_without_access_cannot_delete_class_or_shift(self):
        self.client.force_login(self.no_access_user)
        class_response = self.client.post(
            reverse("students:class_delete", args=[self.class_a.pk])
        )
        shift_response = self.client.post(
            reverse("students:shift_delete", args=[self.shift_a.pk])
        )
        self.assertEqual(class_response.status_code, 403)
        self.assertEqual(shift_response.status_code, 403)
        self.assertTrue(ClassGroup.objects.filter(pk=self.class_a.pk).exists())
        self.assertTrue(Shift.objects.filter(pk=self.shift_a.pk).exists())

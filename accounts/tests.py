from rest_framework.test import APITestCase

from accounts.models import User
from payments.models import PaymentMethod


class AccountApiTests(APITestCase):
    def test_login_returns_tokens_for_matching_account_role(self):
        User.objects.create_user(
            email="passenger@example.com",
            password="SafePassphrase2026!",
            first_name="Aline",
            role=User.Role.PASSENGER,
            phone_number="+250788123456",
        )

        response = self.client.post(
            "/api/v1/auth/login/",
            {
                "email": "passenger@example.com",
                "password": "SafePassphrase2026!",
                "role": "passenger",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn("access", response.data["tokens"])

    def test_passenger_registration_returns_tokens_and_default_cash_method(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "email": "passenger@example.com",
                "password": "SafePassphrase2026!",
                "full_name": "Aline Uwase",
                "phone_number": "0788123456",
                "role": "passenger",
                "preferred_language": "rw",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertIn("access", response.data["tokens"])
        self.assertEqual(response.data["user"]["full_name"], "Aline Uwase")
        self.assertEqual(response.data["user"]["preferred_language"], "rw")
        self.assertTrue(
            PaymentMethod.objects.filter(
                user__email="passenger@example.com",
                kind=PaymentMethod.Kind.CASH,
                is_default=True,
            ).exists()
        )

    def test_public_registration_rejects_admin_role(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "email": "admin@example.com",
                "password": "SafePassphrase2026!",
                "full_name": "Not Admin",
                "phone_number": "0788123456",
                "role": "admin",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_profile_language_preference_can_be_updated(self):
        user = User.objects.create_user(
            email="language@example.com",
            password="SafePassphrase2026!",
            phone_number="+250788123456",
        )
        self.client.force_authenticate(user=user)

        response = self.client.patch(
            "/api/v1/profile/",
            {"preferred_language": "fr"},
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["preferred_language"], "fr")

from django.test import RequestFactory, TestCase
from rest_framework.response import Response
from rest_framework.test import APIClient

from core.middleware import ApiLanguageMiddleware


class LanguageApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_language_list_uses_requested_supported_language(self):
        response = self.client.get(
            "/api/v1/languages/", HTTP_ACCEPT_LANGUAGE="fr-FR,fr;q=0.9"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Language"], "fr")
        self.assertEqual(response.data["current"], "fr")
        self.assertEqual(
            {language["code"] for language in response.data["languages"]},
            {"rw", "en", "fr"},
        )

    def test_unsupported_language_falls_back_to_english(self):
        response = self.client.get(
            "/api/v1/languages/", HTTP_ACCEPT_LANGUAGE="es-ES,es;q=0.9"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Language"], "en")
        self.assertEqual(response.data["current"], "en")

    def test_language_negotiation_uses_supported_lower_priority_language(self):
        response = self.client.get(
            "/api/v1/languages/",
            HTTP_ACCEPT_LANGUAGE="es-ES,fr;q=0.9,en;q=0.8",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Language"], "fr")
        self.assertEqual(response.data["current"], "fr")

    def test_api_error_detail_is_localized(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "", "password": ""},
            format="json",
            HTTP_ACCEPT_LANGUAGE="rw",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response["Content-Language"], "rw")
        self.assertEqual(response.data["detail"], "Imeyili n’ijambo ry’ibanga birakenewe.")

    def test_success_message_is_localized(self):
        middleware = ApiLanguageMiddleware(
            lambda request: Response({"detail": "Verification code sent."})
        )
        response = middleware(
            RequestFactory().get("/", HTTP_ACCEPT_LANGUAGE="fr")
        )

        self.assertEqual(response.data["detail"], "Le code de vérification a été envoyé.")
        self.assertEqual(response["Content-Language"], "fr")

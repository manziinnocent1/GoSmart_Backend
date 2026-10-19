from django.conf import settings
from django.utils.cache import patch_vary_headers
from django.utils import translation

from .languages import translate_api_message


def _select_language(request, supported):
    query_language = request.GET.get("lang")
    if query_language:
        code = query_language.strip().lower().split("-", 1)[0]
        return code if code in supported else settings.LANGUAGE_CODE

    candidates = []
    for index, preference in enumerate(
        request.headers.get("Accept-Language", "").split(",")
    ):
        parts = preference.split(";")
        code = parts[0].strip().lower().split("-", 1)[0]
        if not code:
            continue
        quality = 1.0
        if len(parts) > 1 and parts[1].strip().startswith("q="):
            try:
                quality = float(parts[1].strip()[2:])
            except ValueError:
                quality = 0
        if quality > 0:
            candidates.append((quality, -index, code))

    for _, _, code in sorted(candidates, reverse=True):
        if code in supported:
            return code
    return settings.LANGUAGE_CODE


def _translate_response_details(data, language):
    if isinstance(data, dict):
        return {
            key: (
                translate_api_message(value, language)
                if key in {"detail", "message"} and isinstance(value, str)
                else _translate_response_details(value, language)
            )
            for key, value in data.items()
        }
    if isinstance(data, list):
        return [_translate_response_details(value, language) for value in data]
    return data


class ApiLanguageMiddleware:
    """Select a supported API language from Accept-Language or ?lang=."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        supported = dict(settings.LANGUAGES)
        language = _select_language(request, supported)
        with translation.override(language):
            request.LANGUAGE_CODE = language
            response = self.get_response(request)
        if response.status_code < 400 and hasattr(response, "data"):
            response.data = _translate_response_details(response.data, language)
        response["Content-Language"] = language
        patch_vary_headers(response, ("Accept-Language",))
        return response

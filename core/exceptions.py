from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler

from .languages import translate_api_message


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "The requested action conflicts with the current resource state."
    default_code = "conflict"


def _translate_data(data, language):
    if isinstance(data, dict):
        return {key: _translate_data(value, language) for key, value in data.items()}
    if isinstance(data, list):
        return [_translate_data(value, language) for value in data]
    if isinstance(data, str):
        return translate_api_message(data, language)
    return data


def localized_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None
    request = context.get("request")
    language = getattr(request, "LANGUAGE_CODE", "en")
    response.data = _translate_data(response.data, language)
    response["Content-Language"] = language
    return response

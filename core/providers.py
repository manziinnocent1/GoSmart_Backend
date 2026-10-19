import json
import os
import urllib.error
import urllib.request

from rest_framework.exceptions import APIException


class ProviderUnavailable(APIException):
    status_code = 503
    default_detail = "The payment or messaging provider is currently unavailable."
    default_code = "provider_unavailable"


def post_json(url, payload, api_key):
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except (
        urllib.error.HTTPError,
        urllib.error.URLError,
        TimeoutError,
        json.JSONDecodeError,
    ) as exc:
        raise ProviderUnavailable("The configured provider request failed.") from exc
    if not isinstance(response_data, dict):
        raise ProviderUnavailable("The configured provider returned an invalid response.")
    return response_data

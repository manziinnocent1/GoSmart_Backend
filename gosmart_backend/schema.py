APP_PREFIXES = {
    "Core": ("health", "languages", "saved-places", "emergency-alerts"),
    "Accounts": ("auth", "profile"),
    "Rides": ("fares", "rides"),
    "Payments": ("payment-methods", "payments"),
    "Drivers": ("driver",),
    "Support": ("support",),
    "Operations": ("admin",),
}


def tag_endpoints_by_app(result, generator, request, public):
    for path, path_item in result["paths"].items():
        parts = path.strip("/").split("/")
        api_parts = parts[2:] if parts[:2] == ["api", "v1"] else parts
        app = next(
            (
                app
                for app, prefixes in APP_PREFIXES.items()
                if api_parts and api_parts[0] in prefixes
            ),
            None,
        )
        if app:
            for operation in path_item.values():
                if isinstance(operation, dict) and "operationId" in operation:
                    operation["tags"] = [app]

    return result

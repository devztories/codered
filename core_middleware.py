
from django.shortcuts import render


class ServiceUnavailablePageMiddleware:
    """Replace plain 503 responses with the branded service-unavailable page."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if response.status_code == 503:
            return render(
                request,
                "errors/503.html",
                status=503
            )

        return response


class NoStoreHtmlMiddleware:
    """
    Prevent browsers from restoring stale HTML forms from cache
    after successful submissions and redirects.
    Static and media assets are untouched.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        content_type = response.get("Content-Type", "").lower()

        if content_type.startswith("text/html"):
            response["Cache-Control"] = (
                "private, no-store, no-cache, must-revalidate, max-age=0"
            )
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"

        return response

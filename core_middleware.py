
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import select_template


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

        # Any other error that has no body of its own (for example a 405 from
        # a view restricted to POST, or a 502/504 raised by a proxy) gets the
        # matching branded template, or the generic one when none exists.
        status = response.status_code
        if (
            status >= 400
            and not getattr(response, "streaming", False)
            and not response.content
            and response.get("Content-Type", "").lower().startswith("text/html")
        ):
            template = select_template([f"errors/{status}.html", "errors/error.html"])
            return HttpResponse(
                template.render({"status_code": status}, request),
                status=status,
                headers={k: v for k, v in response.items() if k.lower() == "allow"},
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



class NoStoreHtmlMiddleware:
    """
    Prevent browsers from restoring stale HTML forms from cache after
    successful submissions and redirects. Static/media assets are untouched.
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

from django.shortcuts import render


class ServiceUnavailablePageMiddleware:
    """Replace plain 503 responses with the branded service-unavailable page."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 503:
            return render(request, "errors/503.html", status=503)
        return response



class NoStoreHtmlMiddleware:
    """Prevent stale form pages from reappearing from the browser cache."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Apply only to HTML responses; static assets keep normal caching.
        if response.get("Content-Type", "").lower().startswith("text/html"):
            response["Cache-Control"] = "private, no-store, no-cache, must-revalidate, max-age=0"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"

        return response

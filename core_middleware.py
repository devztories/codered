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

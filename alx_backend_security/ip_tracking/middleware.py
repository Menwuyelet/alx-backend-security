from .models import RequestLog, BlockedIP
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.core.cache import cache
from django_ip_geolocation.middleware import get_geolocation
from .models import RequestLog

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        ip = self.get_client_ip(request)
        path = request.path

        # Check cache first
        geo_data = cache.get(f"geo:{ip}")
        if not geo_data:
            try:
                geo_info = get_geolocation(ip)
                geo_data = {
                    "country": geo_info.get("country_name"),
                    "city": geo_info.get("city"),
                }
            except Exception:
                geo_data = {"country": None, "city": None}

            # Cache for 24 hours
            cache.set(f"geo:{ip}", geo_data, timeout=60 * 60 * 24)

        # Save request log
        RequestLog.objects.create(
            ip_address=ip,
            path=path,
            timestamp=timezone.now(),
            country=geo_data.get("country"),
            city=geo_data.get("city"),
        )

        return response

    def get_client_ip(self, request):
        """Extract client IP, handling proxies if needed."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class IPBlockerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = self.get_client_ip(request)

        if BlockedIP.objects.filter(ip_address=ip).exists():
            return HttpResponseForbidden("Your IP is blocked.")

        return self.get_response(request)

    def get_client_ip(self, request):
        """Get client IP address, handling proxies if needed."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from .models import RequestLog, SuspiciousIP

SENSITIVE_PATHS = ["/admin", "/login"]

@shared_task
def detect_suspicious_ips():
    one_hour_ago = timezone.now() - timedelta(hours=1)

    # 1. Flag IPs exceeding 100 requests/hour
    high_volume_ips = (
        RequestLog.objects.filter(timestamp__gte=one_hour_ago)
        .values("ip_address")
        .annotate(request_count=Count("id"))
        .filter(request_count__gt=100)
    )

    for entry in high_volume_ips:
        ip = entry["ip_address"]
        SuspiciousIP.objects.get_or_create(
            ip_address=ip,
            reason="Excessive requests (>100/hour)",
        )

    # 2. Flag IPs accessing sensitive paths
    suspicious_requests = RequestLog.objects.filter(
        timestamp__gte=one_hour_ago, path__in=SENSITIVE_PATHS
    )

    for req in suspicious_requests:
        SuspiciousIP.objects.get_or_create(
            ip_address=req.ip_address,
            reason=f"Accessed sensitive path: {req.path}",
        )

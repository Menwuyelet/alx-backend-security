def user_or_ip(request):
    if request.user.is_authenticated:
        return str(request.user.id)
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
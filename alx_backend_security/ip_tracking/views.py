from django.http import JsonResponse
from ratelimit.decorators import ratelimit
from .utils import user_or_ip

@ratelimit(key="ip", rate="5/m", method="POST", block=True)
@ratelimit(key=user_or_ip, rate="10/m", method="POST", block=True)
def login_view(request):
    if request.method == "POST":
        # Dummy login for demonstration
        return JsonResponse({"message": "Login attempt"})
    return JsonResponse({"detail": "Method not allowed"}, status=405)
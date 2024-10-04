# myapp/middleware.py
from django.http import HttpResponsePermanentRedirect
from django.conf import settings

class SSLRedirectExcludeWebSocketMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 웹소켓 요청에 대해서는 리다이렉트 방지
        if request.path.startswith("/ws/"):
            return self.get_response(request)

        # 일반 요청에 대해 HTTPS 리다이렉션 적용
        if not request.is_secure() and settings.SECURE_SSL_REDIRECT:
            return HttpResponsePermanentRedirect(f"https://{request.get_host()}{request.get_full_path()}")

        return self.get_response(request)
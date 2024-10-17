# myapp/middleware.py
# from django.http import HttpResponsePermanentRedirect
# from django.conf import settings

# class SSLRedirectExcludeWebSocketMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         # 웹소켓 요청에 대해서는 리다이렉트 방지
#         if request.path.startswith("/ws/"):
#             return self.get_response(request)

#         # 일반 요청에 대해 HTTPS 리다이렉션 적용
#         if not request.is_secure() and settings.SECURE_SSL_REDIRECT:
#             return HttpResponsePermanentRedirect(f"https://{request.get_host()}{request.get_full_path()}")

#         return self.get_response(request)



from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

User = get_user_model()

@database_sync_to_async
def get_user(token_key):
    try:
        token = AccessToken(token_key)
        return User.objects.get(id=token['user_id'])
    except Exception as e:
        return AnonymousUser()

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # 쿼리 스트링에서 토큰을 가져옵니다.
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]

        if token:
            # 토큰이 있으면 사용자를 가져옵니다.
            scope['user'] = await get_user(token)
        else:
            # 토큰이 없으면 AnonymousUser로 설정합니다.
            scope['user'] = AnonymousUser()

        # 기본 미들웨어의 __call__ 메서드를 호출합니다.
        return await super().__call__(scope, receive, send)
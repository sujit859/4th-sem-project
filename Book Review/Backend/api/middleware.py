from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin
from api.helpers import verify_token
from api.models import User

class TokenAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        auth_header = request.headers.get('Authorization')
        request.user = AnonymousUser()
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            payload = verify_token(token)
            if payload:
                try:
                    user = User.objects.get(id=payload['user_id'])
                    if user.status == 'active':
                        request.user = user
                except User.DoesNotExist:
                    pass

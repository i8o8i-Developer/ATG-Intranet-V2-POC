from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailOrUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        login = username or kwargs.get("email") or kwargs.get("username")
        if not login or not password:
            return None
        user_model = get_user_model()
        user = user_model.objects.filter(username__iexact=login).first() or user_model.objects.filter(email__iexact=login).first()
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

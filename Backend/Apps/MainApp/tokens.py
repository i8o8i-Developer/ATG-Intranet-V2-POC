from django.core import signing


def get_secret_key(token_obj, expires_sec=604800):
    return signing.dumps({"id": getattr(token_obj, "id", token_obj)}, salt="mainapp-offer")


def verify_secret_key(token, expires_sec=604800):
    return signing.loads(token, salt="mainapp-offer", max_age=expires_sec)


def env_var():
    return "MAINAPP_SECRET"
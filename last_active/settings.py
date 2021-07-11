from django.conf import settings

LAST_SEEN_DEFAULT_MODULE = getattr(settings, "LAST_SEEN_DEFAULT_MODULE", "default")
LAST_SEEN_INTERVAL = getattr(settings, "LAST_SEEN_INTERVAL", 60 * 60 * 2)

AUTH_USER_MODEL = getattr(settings, "AUTH_USER_MODEL", "auth.User")

from django.conf import settings
from django.utils import translation
from django.utils.deprecation import MiddlewareMixin


class UserLanguageMiddleware(MiddlewareMixin):
    """Activate the user's saved language preference.

    Uses process_view (runs AFTER URL resolution) to activate the language
    for template rendering without breaking i18n_patterns URL matching.
    Sets the language cookie so LocaleMiddleware handles prefix redirects.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated and hasattr(request.user, "language"):
            cookie_lang = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
            user_lang = request.user.language

            # If the cookie was changed (e.g. via set_language view), sync to DB
            if cookie_lang and cookie_lang != user_lang and cookie_lang in dict(settings.LANGUAGES):
                request.user.language = cookie_lang
                request.user.save(update_fields=["language"])
                user_lang = cookie_lang

            translation.activate(user_lang)
            request.LANGUAGE_CODE = user_lang
        return None

    def process_response(self, request, response):
        if hasattr(request, "user") and request.user.is_authenticated and hasattr(request.user, "language"):
            lang = request.user.language
            cookie_lang = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
            if cookie_lang != lang:
                response.set_cookie(
                    settings.LANGUAGE_COOKIE_NAME,
                    lang,
                    max_age=365 * 24 * 60 * 60,
                    path=settings.LANGUAGE_COOKIE_PATH,
                    domain=settings.LANGUAGE_COOKIE_DOMAIN,
                    secure=settings.LANGUAGE_COOKIE_SECURE,
                    httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
                    samesite=settings.LANGUAGE_COOKIE_SAMESITE,
                )
        return response

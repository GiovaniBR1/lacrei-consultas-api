"""Trava os settings de borda dos ambientes remotos (staging e produção)."""

from importlib import import_module

from django.test import SimpleTestCase

AMBIENTES = ("config.settings.staging", "config.settings.production")


class SettingsDeAmbienteRemotoTests(SimpleTestCase):
    def test_debug_desligado(self) -> None:
        for modulo in AMBIENTES:
            with self.subTest(modulo=modulo):
                self.assertIs(import_module(modulo).DEBUG, False)

    def test_cors_nao_libera_qualquer_origem(self) -> None:
        for modulo in AMBIENTES:
            with self.subTest(modulo=modulo):
                self.assertIs(import_module(modulo).CORS_ALLOW_ALL_ORIGINS, False)

    def test_proxy_ssl_header_do_render(self) -> None:
        for modulo in AMBIENTES:
            with self.subTest(modulo=modulo):
                self.assertEqual(
                    import_module(modulo).SECURE_PROXY_SSL_HEADER,
                    ("HTTP_X_FORWARDED_PROTO", "https"),
                )

    def test_cookies_e_redirect_https(self) -> None:
        for modulo in AMBIENTES:
            with self.subTest(modulo=modulo):
                settings_do_ambiente = import_module(modulo)
                self.assertIs(settings_do_ambiente.SECURE_SSL_REDIRECT, True)
                self.assertIs(settings_do_ambiente.SESSION_COOKIE_SECURE, True)
                self.assertIs(settings_do_ambiente.CSRF_COOKIE_SECURE, True)

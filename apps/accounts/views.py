"""Views de autenticação."""

from __future__ import annotations

from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView


class TokenObtainPairThrottledView(TokenObtainPairView):
    """Emissão de token sob escopo próprio, mais estrito que o tráfego autenticado."""

    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth_token"

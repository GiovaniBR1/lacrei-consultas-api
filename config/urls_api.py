"""Rotas versionadas /api/v1/."""

from apps.accounts.views import TokenObtainPairThrottledView
from apps.consultas.views import ConsultaViewSet
from apps.payments.views import CobrancaCreateView
from apps.profissionais.views import ProfissionalViewSet
from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register("profissionais", ProfissionalViewSet, basename="profissional")
router.register("consultas", ConsultaViewSet, basename="consulta")

urlpatterns = [
    path("auth/token/", TokenObtainPairThrottledView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "consultas/<uuid:consulta_id>/cobrancas/",
        CobrancaCreateView.as_view(),
        name="consulta-cobrancas",
    ),
    *router.urls,
]

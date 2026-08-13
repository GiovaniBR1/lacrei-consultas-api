"""Rotas versionadas /api/v1/."""

from apps.consultas.views import ConsultaViewSet
from apps.profissionais.views import ProfissionalViewSet
from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register("profissionais", ProfissionalViewSet, basename="profissional")
router.register("consultas", ConsultaViewSet, basename="consulta")

urlpatterns = [
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    *router.urls,
]

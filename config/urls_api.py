"""Rotas versionadas /api/v1/."""

from apps.consultas.views import ConsultaViewSet
from apps.profissionais.views import ProfissionalViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("profissionais", ProfissionalViewSet, basename="profissional")
router.register("consultas", ConsultaViewSet, basename="consulta")

urlpatterns = router.urls

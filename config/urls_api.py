"""Rotas versionadas /api/v1/."""

from apps.profissionais.views import ProfissionalViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("profissionais", ProfissionalViewSet, basename="profissional")

urlpatterns = router.urls

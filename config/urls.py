from apps.core.views import HealthView, ReadyView, SchemaView, SwaggerView
from apps.payments.views import WebhookAsaasView
from django.urls import include, path

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("ready/", ReadyView.as_view(), name="ready"),
    path("webhooks/asaas/", WebhookAsaasView.as_view(), name="webhook-asaas"),
    path("api/schema/", SchemaView.as_view(), name="schema"),
    path("api/docs/", SwaggerView.as_view(url_name="schema"), name="docs"),
    path("api/v1/", include("config.urls_api")),
]

from apps.core.views import HealthView, ReadyView
from django.urls import include, path

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("ready/", ReadyView.as_view(), name="ready"),
    path("api/v1/", include("config.urls_api")),
]

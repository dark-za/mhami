from __future__ import annotations

from django.http import JsonResponse
from django.urls import path


def live(_request):
    return JsonResponse({"status": "ok"})


def ready(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("live", live),
    path("ready", ready),
]

from django.urls import path

from .views import InitialSetupView


urlpatterns = [
    path("initialize", InitialSetupView.as_view()),
]

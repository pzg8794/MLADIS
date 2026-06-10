from django.urls import path

from .views import WorkboardView


app_name = "operations"

urlpatterns = [
    path("workboard/", WorkboardView.as_view(), name="workboard"),
]

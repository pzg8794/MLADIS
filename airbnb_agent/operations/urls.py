from django.urls import path

from .views import MaintenanceWorkItemView, WorkboardView


app_name = "operations"

urlpatterns = [
    path("workboard/", WorkboardView.as_view(), name="workboard"),
    path("maintenance/", MaintenanceWorkItemView.as_view(), name="maintenance"),
]

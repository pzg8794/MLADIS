from django.urls import path

from .views import ModernOperationsWorkboardView, OpsWorkboardAPIView, OpsWorkItemCompletionAPIView


app_name = "operations"

urlpatterns = [
    path("ops/workboard/", ModernOperationsWorkboardView.as_view(), name="workboard"),
    path("api/ops/workboard/", OpsWorkboardAPIView.as_view(), name="workboard-api"),
    path("api/ops/workboard/items/<int:pk>/completion/", OpsWorkItemCompletionAPIView.as_view(), name="workitem-completion-api"),
]

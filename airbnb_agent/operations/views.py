import json

from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView

from .services import WorkboardService


class OwnerWorkboardAccessMixin:
    def dispatch(self, request, *args, **kwargs):
        try:
            WorkboardService().access_policy.require_owner(request.user)
        except PermissionDenied as error:
            return JsonResponse({"error": str(error)}, status=403)
        return super().dispatch(request, *args, **kwargs)


class ModernOperationsWorkboardView(OwnerWorkboardAccessMixin, TemplateView):
    template_name = "bookings/modern_dashboard.html"


class OpsWorkboardAPIView(OwnerWorkboardAccessMixin, View):
    def get(self, request):
        return JsonResponse(WorkboardService().snapshot_for(request.user))


class OpsWorkItemCompletionAPIView(OwnerWorkboardAccessMixin, View):
    def post(self, request, pk):
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)

        item = WorkboardService().set_completion(
            request.user,
            pk,
            completed=bool(payload.get("completed")),
        )
        return JsonResponse({"ok": True, "item": item})

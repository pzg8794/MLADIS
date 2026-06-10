from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import TemplateView

from .services import WorkboardService


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff


class WorkboardView(StaffRequiredMixin, TemplateView):
    template_name = "operations/workboard.html"
    service_class = WorkboardService

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.service_class().get_board_context())
        return context

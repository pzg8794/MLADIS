from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import TemplateView

from .access import is_operations_owner
from .services import WorkboardService


class OperationsOwnerRequiredMixin(UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        return is_operations_owner(self.request.user)


class WorkboardView(OperationsOwnerRequiredMixin, TemplateView):
    template_name = "operations/workboard.html"
    service_class = WorkboardService

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.service_class().get_board_context())
        return context

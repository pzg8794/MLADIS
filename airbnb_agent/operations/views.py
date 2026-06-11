from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView

from .access import is_operations_owner
from .forms import WorkItemForm
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


class MaintenanceWorkItemView(OperationsOwnerRequiredMixin, TemplateView):
    template_name = "operations/maintenance.html"
    form_class = WorkItemForm
    service_class = WorkboardService

    def get_form(self):
        return self.form_class(data=self.request.POST or None)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = kwargs.get("form") or self.get_form()
        context.update(self.service_class().get_board_context())
        context["form"] = form
        context["maintenance_items"] = [
            item
            for column in context["columns"]
            for item in column["items"]
            if item.neuron in {"booking", "finance", "operations"}
        ]
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        work_item = form.save(commit=False)
        work_item.created_by = request.user
        if not work_item.item_id and work_item.inquiry_id and work_item.inquiry.item_id:
            work_item.item = work_item.inquiry.item
        work_item.save()
        messages.success(request, "Work item attached to the selected booking context.")
        return redirect("operations:maintenance")

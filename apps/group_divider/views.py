from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView
from .services.group_split import group_split as group_split_f
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.group_maker.models import GroupCreationModel
from django.shortcuts import render, get_object_or_404
from .forms import GroupMakerForm


from django.urls import reverse_lazy

class GroupDividerHome(LoginRequiredMixin, TemplateView):
    template_name = "group_divider/home.html"
    form_class = GroupMakerForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["groups"] = GroupCreationModel.objects.filter(user=self.request.user)
        context["form"] = self.form_class()
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            selected_group_id = request.POST.get(
                "group_id"
            )  # tag: select, field: name="group_id"
            selected_group_size = form.cleaned_data["size"]
            selected_group = get_object_or_404(
                GroupCreationModel, id=selected_group_id, user=request.user
            )
            selected_group_members = selected_group.get_members_list()
            splitted_group = group_split_f(selected_group_members, selected_group_size)
            groups = GroupCreationModel.objects.filter(user=self.request.user)

            return render(
                request,
                "group_divider/home.html",
                {
                    "form": form,
                    "splitted_group": splitted_group,
                    "selected_group": selected_group,
                    "groups": groups,
                },
            )
        return render(request, "group_divider/home.html", {"form": form})
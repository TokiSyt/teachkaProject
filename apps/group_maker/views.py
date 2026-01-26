from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView
from .services.group_split import group_split as group_split_f
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from .forms import GroupCreationForm, GroupMakerForm
from .models import GroupCreationModel
from django.urls import reverse_lazy


class GroupMakerHome(LoginRequiredMixin, TemplateView):
    template_name = "group_maker/home.html"
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
                "group_maker/home.html",
                {
                    "form": form,
                    "splitted_group": splitted_group,
                    "selected_group": selected_group,
                    "groups": groups,
                },
            )
        return render(request, "group_maker/home.html", {"form": form})


class GroupMakerListCreate(LoginRequiredMixin, CreateView):
    model = GroupCreationModel
    template_name = "group_maker/list_create.html"
    form_class = GroupCreationForm

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("home")


class GroupMakerListUpdate(LoginRequiredMixin, UpdateView):
    model = GroupCreationModel
    template_name = "group_maker/list_edit.html"
    form_class = GroupCreationForm

    def get_success_url(self):
        return reverse_lazy("home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_group"] = self.object
        return context


class GroupMakerListDelete(LoginRequiredMixin, DeleteView):
    model = GroupCreationModel
    template_name = "group_maker/confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_group"] = self.object
        return context

from django.contrib.auth.mixins import LoginRequiredMixin
from .services.utils import choose_a_random_name
from apps.group_maker.models import GroupCreationModel
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "wheel/home.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["groups"] = GroupCreationModel.objects.filter(user=self.request.user)
        return context
    
    def get(self, request, *args, **kwargs):
        selected_group = None
        
        if "reset" in request.GET:
            for key in list(request.session.keys()):
                if key.startswith("already_chosen_names_"):
                    request.session.pop(key, None)
                request.session.modified = True
                
        selected_group_id = request.GET.get("group_id")       
        if selected_group_id:
            selected_group = get_object_or_404(GroupCreationModel, id=selected_group_id, user=request.user)
        
        context = self.get_context_data(**kwargs)
        if selected_group:
            context["selected_group"] = selected_group
        return self.render_to_response(context)
    
    def post(self, request, *args, **kwargs):
        
        groups = GroupCreationModel.objects.filter(user=self.request.user)
        selected_group_id = request.POST.get(
            "group_id"
        )  # tag: select, field: name="group_id"
        
        if selected_group_id:
            selected_group = get_object_or_404(
                GroupCreationModel, id=selected_group_id, user=request.user
            )
            selected_group_members = selected_group.get_members_list()
            selected_group_size = selected_group.get_size()
            
            session_key = f"already_chosen_names_{selected_group.id}"
            already_chosen_names = request.session.get(session_key, [])
            
            if len(already_chosen_names) >= selected_group_size:
                return render(
                request,
                self.template_name,
                {
                    "chosen_name": None,
                    "already_chosen_names": already_chosen_names,
                    "selected_group": selected_group,
                    "groups": groups,
                    "message": "All names have been chosen!",
                },
            )
                
            chosen_name, already_chosen_names = choose_a_random_name(selected_group_members, already_chosen_names)
            request.session[session_key] = already_chosen_names
            request.session.modified = True
            
            return render(
                request,
                self.template_name,
                {
                    "chosen_name": chosen_name,
                    "already_chosen_names": already_chosen_names,
                    "selected_group": selected_group,
                    "groups": groups,
                },
            )
                
        return render(request, "wheel/home.html")
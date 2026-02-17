from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.generic import FormView, TemplateView

from apps.users.models import UserStats

from .forms import CountdownmForm


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "timer/home.html"


class StopwatchView(LoginRequiredMixin, TemplateView):
    template_name = "timer/stopwatch.html"

    def post(self, request):
        action = request.POST.get("action")
        stats, _ = UserStats.objects.get_or_create(user=request.user)

        if action == "start":
            stats.stopwatch_starts += 1
            stats.save(update_fields=["stopwatch_starts"])
        elif action == "flag":
            stats.stopwatch_flags += 1
            stats.save(update_fields=["stopwatch_flags"])
        elif action == "stop":
            elapsed = int(request.POST.get("elapsed", 0))
            if elapsed > 0:
                stats.stopwatch_total_ms += elapsed
                stats.save(update_fields=["stopwatch_total_ms"])
        else:
            return JsonResponse({"status": "error"}, status=400)

        return JsonResponse({"status": "ok"})


class TimerView(LoginRequiredMixin, FormView):
    form_class = CountdownmForm
    template_name = "timer/countdown.html"

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        stats, _ = UserStats.objects.get_or_create(user=request.user)

        if action == "start":
            stats.countdown_starts += 1
            stats.save(update_fields=["countdown_starts"])
        elif action == "stop":
            elapsed = int(request.POST.get("elapsed", 0))
            if elapsed > 0:
                stats.countdown_total_ms += elapsed
                stats.save(update_fields=["countdown_total_ms"])
        else:
            return JsonResponse({"status": "error"}, status=400)

        return JsonResponse({"status": "ok"})

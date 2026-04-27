import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.core.mixins import FormUserMixin, UserOwnedMixin

from .forms import QuizForm, RoundForm
from .models import Answer, Quiz, Round


class HomeView(LoginRequiredMixin, ListView):
    model = Quiz
    template_name = "quizzmaker/home.html"
    context_object_name = "quizzes"
    paginate_by = 24

    def get_template_names(self):
        if self.request.GET.get("partial"):
            return ["quizzmaker/_quiz_region.html"]
        return [self.template_name]

    def get(self, request, *args, **kwargs):
        if request.GET.get("scope") == "mine" and not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        scope = self.request.GET.get("scope", "public")
        q = self.request.GET.get("q", "").strip()

        if scope == "mine" and self.request.user.is_authenticated:
            qs = Quiz.objects.filter(user=self.request.user)
        else:
            scope = "public"
            qs = Quiz.objects.filter(visibility=Quiz.PUBLIC)

        if q:
            qs = qs.filter(title__icontains=q)

        self._scope = scope
        return (
            qs.select_related("user")
            .annotate(timeless_rounds=Count("rounds", filter=Q(rounds__time_limit=0)))
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["scope"] = getattr(self, "_scope", "public")
        ctx["query"] = self.request.GET.get("q", "")
        return ctx


class QuizCreateView(LoginRequiredMixin, FormUserMixin, CreateView):
    model = Quiz
    form_class = QuizForm
    template_name = "quizzmaker/quiz_form.html"

    def get_success_url(self):
        return reverse("quizzmaker:rounds", kwargs={"pk": self.object.pk})


class QuizUpdateView(UserOwnedMixin, UpdateView):
    model = Quiz
    form_class = QuizForm
    http_method_names = ["post"]

    def get_success_url(self):
        return reverse("quizzmaker:rounds", kwargs={"pk": self.object.pk})

    def form_invalid(self, form):
        _flash_form_errors(self.request, form)
        return redirect(self.get_success_url())


class RoundEditorView(UserOwnedMixin, DetailView):
    model = Quiz
    template_name = "quizzmaker/round_editor.html"
    context_object_name = "quiz"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        rounds = list(self.object.rounds.prefetch_related("answers"))
        ctx["rounds"] = rounds
        ctx["round_form"] = RoundForm()
        ctx["next_round_title"] = f"Round {len(rounds) + 1}"

        selected = None
        sel_pos = self.request.GET.get("round")
        if sel_pos and sel_pos.isdigit():
            idx = int(sel_pos) - 1
            if 0 <= idx < len(rounds):
                selected = rounds[idx]
        if selected is None and rounds:
            selected = rounds[0]
        ctx["selected_round"] = selected
        return ctx


def _round_position(quiz, round_pk):
    for idx, r in enumerate(quiz.rounds.all(), start=1):
        if r.pk == round_pk:
            return idx
    return 1


def _seed_answers(round_obj):
    """Ensure round has the expected number of blank answer slots for its type.

    Idempotent: only creates rows missing slots; never deletes existing answers.
    """
    if round_obj.question_type == Round.SELECT_CORRECT:
        existing = round_obj.answers.count()
        for i in range(existing, 4):
            Answer.objects.create(round=round_obj, order=i + 1, text="")
    elif round_obj.question_type == Round.TYPE_INPUT:
        if round_obj.answers.count() == 0:
            Answer.objects.create(round=round_obj, order=1, text="")


def _flash_form_errors(request, form):
    for field, errs in form.errors.items():
        label = field.replace("_", " ").title()
        for err in errs:
            messages.error(request, f"{label}: {err}")


class RoundCreateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        quiz = get_object_or_404(Quiz, pk=pk, user=request.user)
        form = RoundForm(request.POST, request.FILES)
        new_pk = None
        if form.is_valid():
            count = quiz.rounds.count()
            round_obj = form.save(commit=False)
            round_obj.quiz = quiz
            round_obj.order = count + 1
            round_obj.save()
            _seed_answers(round_obj)
            new_pk = round_obj.pk
            quiz.recalculate_totals()
        else:
            _flash_form_errors(request, form)
        url = reverse("quizzmaker:rounds", kwargs={"pk": quiz.pk})
        if new_pk:
            url += f"?round={_round_position(quiz, new_pk)}"
        return redirect(url)


class RoundUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk, round_pk):
        quiz = get_object_or_404(Quiz, pk=pk, user=request.user)
        round_obj = get_object_or_404(quiz.rounds, pk=round_pk)
        form = RoundForm(request.POST, request.FILES, instance=round_obj)
        if form.is_valid():
            form.save()
            _seed_answers(round_obj)
            quiz.recalculate_totals()
        else:
            _flash_form_errors(request, form)
        url = reverse("quizzmaker:rounds", kwargs={"pk": quiz.pk})
        url += f"?round={_round_position(quiz, round_obj.pk)}"
        return redirect(url)


class RoundDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, round_pk):
        quiz = get_object_or_404(Quiz, pk=pk, user=request.user)
        round_obj = get_object_or_404(quiz.rounds, pk=round_pk)
        with transaction.atomic():
            round_obj.delete()
            for index, r in enumerate(quiz.rounds.all().order_by("order", "id"), start=1):
                if r.order != index:
                    quiz.rounds.filter(pk=r.pk).update(order=index)
            quiz.recalculate_totals()
        return redirect("quizzmaker:rounds", pk=quiz.pk)


class QuizFinalizeView(LoginRequiredMixin, View):
    def post(self, request, pk):
        quiz = get_object_or_404(Quiz, pk=pk, user=request.user)
        quiz.recalculate_totals()
        return redirect("quizzmaker:home")


class AnswerUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk, answer_pk):
        quiz = get_object_or_404(Quiz, pk=pk, user=request.user)
        answer = get_object_or_404(Answer, pk=answer_pk, round__quiz=quiz)
        if "text" in request.POST:
            answer.text = request.POST.get("text", "")
        if "is_correct" in request.POST:
            answer.is_correct = request.POST.get("is_correct") in ("1", "true", "on")
        answer.save()
        return JsonResponse({"ok": True})


class RoundReorderView(LoginRequiredMixin, View):
    def post(self, request, pk):
        quiz = get_object_or_404(Quiz, pk=pk, user=request.user)
        try:
            payload = json.loads(request.body or b"{}")
            ids = [int(x) for x in payload.get("order", [])]
        except (ValueError, TypeError):
            return JsonResponse({"ok": False, "error": "bad payload"}, status=400)

        valid_ids = set(quiz.rounds.values_list("pk", flat=True))
        if set(ids) != valid_ids:
            return JsonResponse({"ok": False, "error": "id mismatch"}, status=400)

        with transaction.atomic():
            for index, round_pk in enumerate(ids, start=1):
                quiz.rounds.filter(pk=round_pk).update(order=index)
        return JsonResponse({"ok": True})

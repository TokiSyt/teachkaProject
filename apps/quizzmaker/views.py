import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from apps.core.mixins import FormUserMixin, UserOwnedMixin

from . import live
from .forms import QuizForm, RoundForm
from .models import Answer, GameSession, Quiz, Round


class HomeView(ListView):
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
        rounds = list(quiz.rounds.prefetch_related("answers"))
        incomplete = [r for r in rounds if not r.has_correct_answer]
        if incomplete:
            for r in incomplete:
                messages.error(
                    request,
                    _("Round %(n)s needs a correct answer before you can save.") % {"n": r.order},
                )
            return redirect("quizzmaker:rounds", pk=quiz.pk)
        quiz.recalculate_totals()
        return redirect("quizzmaker:home")


class QuizDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        quiz = get_object_or_404(Quiz, pk=pk, user=request.user)
        quiz.delete()
        messages.success(request, _("Quiz deleted."))
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


class AnswerCreateView(LoginRequiredMixin, View):
    """Add a new (blank) accepted answer to a round (type_input alternatives)."""

    def post(self, request, pk, round_pk):
        quiz = get_object_or_404(Quiz, pk=pk, user=request.user)
        round_obj = get_object_or_404(quiz.rounds, pk=round_pk)
        order = round_obj.answers.count() + 1
        answer = Answer.objects.create(round=round_obj, order=order, text="")
        return JsonResponse({"ok": True, "pk": answer.pk})


class AnswerDeleteView(LoginRequiredMixin, View):
    """Remove an accepted answer. Never deletes a round's last answer."""

    def post(self, request, pk, answer_pk):
        quiz = get_object_or_404(Quiz, pk=pk, user=request.user)
        answer = get_object_or_404(Answer, pk=answer_pk, round__quiz=quiz)
        if answer.round.answers.count() <= 1:
            return JsonResponse({"ok": False, "error": "last answer"}, status=400)
        answer.delete()
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


# --- live play --------------------------------------------------------------


class HostSessionCreateView(LoginRequiredMixin, View):
    """Launch a live session for a quiz. Any logged-in user may host a public
    quiz; private quizzes only by their owner."""

    def post(self, request, pk):
        quiz = get_object_or_404(Quiz, pk=pk)
        if quiz.visibility == Quiz.PRIVATE and quiz.user_id != request.user.id:
            raise PermissionDenied
        try:
            session = live.create_session(quiz, request.user, show_question_on_device=False)
        except live.LiveError as exc:
            messages.error(request, str(exc))
            return redirect("quizzmaker:home")
        return redirect("quizzmaker:session_host", code=session.code)


class SessionHostView(LoginRequiredMixin, TemplateView):
    """Host/projector screen. Only the session host may open it."""

    template_name = "quizzmaker/session_host.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        code = self.kwargs["code"].upper()
        if not live.session_exists(code):
            raise Http404
        # Code is only unique among live rooms; resolve the row by its pk.
        session = get_object_or_404(GameSession, pk=live.get_meta(code)["session_id"])
        if session.host_id != self.request.user.id:
            raise PermissionDenied
        ctx["session"] = session
        ctx["code"] = session.code
        return ctx


class JoinView(View):
    """Public join: enter code + nickname (no account required)."""

    template_name = "quizzmaker/join.html"

    def get(self, request, code=None):
        # Code in the URL path => known room: lock the field, ask only nickname.
        locked = code is not None
        code = (code or request.GET.get("code", "")).upper()
        nickname = request.user.username if request.user.is_authenticated else ""
        return render(
            request,
            self.template_name,
            {"code": code, "code_locked": locked, "nickname": nickname},
        )

    def post(self, request, code=None):
        code = (request.POST.get("code") or code or "").strip().upper()
        nickname = request.POST.get("nickname", "").strip()
        locked = request.POST.get("code_locked") == "1"
        ctx = {"code": code, "nickname": nickname, "code_locked": locked}
        if not live.session_exists(code):
            ctx["error"] = _("Game not found. Check the code.")
            return render(request, self.template_name, ctx)
        if request.user.is_authenticated and str(request.user.id) == live.get_meta(code).get("host_id"):
            ctx["error"] = _("You're hosting this game. Open it from your host screen.")
            return render(request, self.template_name, ctx)
        try:
            token = live.add_participant(code, nickname, request.user.id if request.user.is_authenticated else None)
        except live.LiveError as exc:
            ctx["error"] = str(exc)
            return render(request, self.template_name, ctx)

        response = redirect("quizzmaker:session_play", code=code)
        response.set_cookie(
            f"quiz_token_{code}",
            token,
            max_age=live.SESSION_TTL,
            httponly=True,
            samesite="Lax",
            secure=request.is_secure(),
        )
        return response


class SessionPlayView(View):
    """Player screen. Requires the participant token cookie from joining."""

    template_name = "quizzmaker/session_play.html"

    def get(self, request, code):
        code = code.upper()
        if not live.session_exists(code):
            raise Http404
        token = request.COOKIES.get(f"quiz_token_{code}")
        if not token or not live.get_participant(code, token):
            return redirect(f"{reverse('quizzmaker:join')}?code={code}")
        return render(request, self.template_name, {"code": code})


class LeaveSessionView(View):
    """Player leaves a game: remove from session, notify host, clear cookie."""

    def post(self, request, code):
        code = code.upper()
        token = request.COOKIES.get(f"quiz_token_{code}")
        if token and live.session_exists(code):
            live.remove_participant(code, token)
            layer = get_channel_layer()
            if layer:
                async_to_sync(layer.group_send)(f"quiz_{code}", {"type": "refresh"})
        response = redirect("quizzmaker:home")
        response.delete_cookie(f"quiz_token_{code}")
        return response

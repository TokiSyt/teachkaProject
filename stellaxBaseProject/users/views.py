from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm


def register(request):

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("home")
    else:
        form = RegisterForm()

    context = {"form": form}

    return render(request, "users/register.html", context)


@login_required
def profileView(request):

    context = {}
    return render(request, "users/profile.html", context)


@login_required
def userSettings(request):

    context = {}
    return render(request, "wip.html", context)

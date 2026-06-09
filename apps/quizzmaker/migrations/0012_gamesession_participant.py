import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("quizzmaker", "0011_remove_round_title"),
    ]

    operations = [
        migrations.CreateModel(
            name="GameSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("code", models.CharField(db_index=True, max_length=8, unique=True)),
                (
                    "state",
                    models.CharField(
                        choices=[("lobby", "Lobby"), ("active", "Active"), ("ended", "Ended")],
                        default="lobby",
                        max_length=8,
                    ),
                ),
                ("show_question_on_device", models.BooleanField(default=False)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                (
                    "host",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="hosted_sessions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "quiz",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sessions",
                        to="quizzmaker.quiz",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Participant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("nickname", models.CharField(max_length=30)),
                ("final_score", models.IntegerField(default=0)),
                ("max_streak", models.PositiveIntegerField(default=0)),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="participants",
                        to="quizzmaker.gamesession",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="quiz_participations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-final_score", "id"]},
        ),
        migrations.AddConstraint(
            model_name="participant",
            constraint=models.UniqueConstraint(fields=("session", "nickname"), name="unique_nickname_per_session"),
        ),
    ]

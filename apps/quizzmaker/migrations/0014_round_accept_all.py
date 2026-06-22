from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("quizzmaker", "0013_gamesession_code_not_unique"),
    ]

    operations = [
        migrations.AddField(
            model_name="round",
            name="accept_all",
            field=models.BooleanField(
                default=False,
                help_text="type_input only: accept every submitted answer as correct (open question).",
            ),
        ),
    ]

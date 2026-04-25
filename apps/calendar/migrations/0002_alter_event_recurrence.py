from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("calendar", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="recurrence",
            field=models.CharField(
                choices=[
                    ("none", "One-time event"),
                    ("daily", "Daily"),
                    ("weekly", "Weekly"),
                    ("monthly", "Monthly"),
                    ("yearly", "Yearly"),
                ],
                default="none",
                max_length=10,
            ),
        ),
    ]

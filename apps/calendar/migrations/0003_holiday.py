from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("calendar", "0002_alter_event_recurrence"),
    ]

    operations = [
        migrations.CreateModel(
            name="Holiday",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=120)),
                ("subject", models.CharField(blank=True, max_length=200)),
                ("description", models.TextField(blank=True)),
                ("date", models.DateField()),
                (
                    "country",
                    models.CharField(
                        choices=[
                            ("CZ", "Czech Republic"),
                            ("PT", "Portugal"),
                            ("EN", "England"),
                            ("INTL", "International"),
                        ],
                        max_length=4,
                    ),
                ),
            ],
            options={
                "ordering": ["date", "name"],
            },
        ),
        migrations.AddIndex(
            model_name="holiday",
            index=models.Index(fields=["country", "date"], name="calendar_ho_country_f2dca1_idx"),
        ),
    ]

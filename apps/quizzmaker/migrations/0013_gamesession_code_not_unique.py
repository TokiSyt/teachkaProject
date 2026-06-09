from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("quizzmaker", "0012_gamesession_participant"),
    ]

    operations = [
        migrations.AlterField(
            model_name="gamesession",
            name="code",
            field=models.CharField(db_index=True, max_length=8),
        ),
    ]

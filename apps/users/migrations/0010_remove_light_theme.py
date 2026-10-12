from django.db import migrations, models


def move_light_users_to_fantasy(apps, schema_editor):
    CustomUser = apps.get_model("users", "CustomUser")
    CustomUser.objects.filter(theme="light").update(theme="fantasy")


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0009_alter_customuser_theme"),
    ]

    operations = [
        migrations.RunPython(move_light_users_to_fantasy, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="customuser",
            name="theme",
            field=models.CharField(
                choices=[
                    ("dark", "Dark"),
                    ("pastel", "Pastel"),
                    ("lemonade", "Editorial"),
                    ("fantasy", "Palette"),
                ],
                default="fantasy",
                max_length=10,
            ),
        ),
    ]

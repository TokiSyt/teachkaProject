from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quizzmaker', '0008_alter_round_question_type_labels'),
    ]

    operations = [
        migrations.AddField(
            model_name='quiz',
            name='focus_x',
            field=models.PositiveSmallIntegerField(default=50),
        ),
        migrations.AddField(
            model_name='quiz',
            name='focus_y',
            field=models.PositiveSmallIntegerField(default=50),
        ),
        migrations.AddField(
            model_name='round',
            name='focus_x',
            field=models.PositiveSmallIntegerField(default=50),
        ),
        migrations.AddField(
            model_name='round',
            name='focus_y',
            field=models.PositiveSmallIntegerField(default=50),
        ),
    ]

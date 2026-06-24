from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quizzmaker', '0015_alter_round_question_type_true_false'),
    ]

    operations = [
        migrations.AddField(
            model_name='quiz',
            name='streak_bonus_rate',
            field=models.PositiveSmallIntegerField(default=10, help_text='Bonus % added per extra streak'),
        ),
        migrations.AddField(
            model_name='quiz',
            name='streak_bonus_cap',
            field=models.PositiveSmallIntegerField(default=50, help_text='Max bonus % (≤100)'),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quizzmaker', '0007_alter_upload_paths'),
    ]

    operations = [
        migrations.AlterField(
            model_name='round',
            name='question_type',
            field=models.CharField(
                choices=[
                    ('select_correct', 'Pick the correct answer'),
                    ('type_input', 'Write the answer'),
                    ('drag_answer', 'Drag the answer into the blank'),
                ],
                default='select_correct',
                max_length=20,
            ),
        ),
    ]

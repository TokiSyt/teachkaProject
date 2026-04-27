from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quizzmaker', '0006_round_question'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quiz',
            name='logo',
            field=models.ImageField(blank=True, null=True, upload_to='uploads/quizzmaker/logos/'),
        ),
        migrations.AlterField(
            model_name='round',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='uploads/quizzmaker/rounds/'),
        ),
    ]

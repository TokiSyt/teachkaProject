# Generated manually for Member model transfer from point_system to core

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Step 2 of Member model transfer: Create Member model in core's state.

    The database table already exists (renamed from point_system_member to core_member
    in point_system migration 0014). This migration only updates Django's state.
    """

    initial = True

    dependencies = [
        ("group_maker", "0001_initial"),
        ("point_system", "0014_move_member_to_core"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="Member",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                        ("name", models.CharField(max_length=50)),
                        ("positive_data", models.JSONField(default=dict)),
                        ("negative_data", models.JSONField(default=dict)),
                        ("positive_total", models.IntegerField(blank=True, default=0)),
                        ("negative_total", models.IntegerField(blank=True, default=0)),
                        (
                            "group",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="members",
                                to="group_maker.groupcreationmodel",
                            ),
                        ),
                    ],
                    options={
                        "ordering": ["id"],
                    },
                ),
            ],
            database_operations=[],
        ),
    ]

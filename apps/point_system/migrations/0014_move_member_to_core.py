# Generated manually for Member model transfer from point_system to core

from django.db import migrations


class Migration(migrations.Migration):
    """
    Step 1 of Member model transfer: Remove from point_system state and rename table.

    Uses SeparateDatabaseAndState to:
    1. Delete Member model from point_system's Django state
    2. Rename database table from point_system_member to core_member
    """

    dependencies = [
        ("point_system", "0013_alter_fielddefinition_type"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(
                    name="Member",
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql='ALTER TABLE "point_system_member" RENAME TO "core_member"',
                    reverse_sql='ALTER TABLE "core_member" RENAME TO "point_system_member"',
                ),
            ],
        ),
    ]

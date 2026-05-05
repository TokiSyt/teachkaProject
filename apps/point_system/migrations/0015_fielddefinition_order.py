from django.db import migrations, models


def backfill_order(apps, schema_editor):
    FieldDefinition = apps.get_model("point_system", "FieldDefinition")
    seen = {}
    for field in FieldDefinition.objects.order_by("group_id", "definition", "created_at", "id"):
        key = (field.group_id, field.definition)
        seen[key] = seen.get(key, 0) + 1
        FieldDefinition.objects.filter(pk=field.pk).update(order=seen[key])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("point_system", "0014_move_member_to_core"),
    ]

    operations = [
        migrations.AddField(
            model_name="fielddefinition",
            name="order",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.RunPython(backfill_order, noop_reverse),
    ]

from __future__ import annotations

from django.db import migrations, models


def disable_unimplemented_encryption(apps, schema_editor):
    apps.get_model("backups", "BackupPolicy").objects.filter(encrypted=True).update(encrypted=False)


class Migration(migrations.Migration):
    dependencies = [("backups", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="backuppolicy",
            name="encrypted",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="backuprun",
            name="artifact_sha256",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="backuprun",
            name="manifest_sha256",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="restorerun",
            name="target_name",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.RunPython(disable_unimplemented_encryption, migrations.RunPython.noop),
    ]

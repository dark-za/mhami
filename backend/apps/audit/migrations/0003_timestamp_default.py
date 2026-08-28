from __future__ import annotations

from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):
    dependencies = [("audit", "0002_tamper_evident_integrity")]

    operations = [
        migrations.AlterField(
            model_name="auditevent",
            name="timestamp",
            field=models.DateTimeField(default=timezone.now, editable=False),
        ),
    ]

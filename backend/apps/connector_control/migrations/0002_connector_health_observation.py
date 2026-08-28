from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("connector_control", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="tenantconnectorenrollment",
            name="health_expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="tenantconnectorenrollment",
            name="health_ttl_seconds",
            field=models.PositiveIntegerField(default=300),
        ),
    ]

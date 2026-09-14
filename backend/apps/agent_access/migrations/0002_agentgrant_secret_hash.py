from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("agent_access", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="agentgrant",
            name="secret_hash",
            field=models.CharField(blank=True, default="", max_length=128),
            preserve_default=False,
        ),
    ]

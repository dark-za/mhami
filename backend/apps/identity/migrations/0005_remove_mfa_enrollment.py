from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("identity", "0004_mfaenrollment_last_used_timestep"),
    ]

    operations = [
        migrations.DeleteModel(name="MfaEnrollment"),
    ]

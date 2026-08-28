from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("ai_gateway", "0001_initial"),
        ("reviews", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="aianalysisrun",
            name="review_decision",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="ai_analysis_runs",
                to="reviews.reviewdecision",
            ),
        ),
        migrations.AddConstraint(
            model_name="aianalysiscriterion",
            constraint=models.CheckConstraint(
                condition=models.Q(("shadow_mode", True), ("auto_pass_enabled", False)),
                name="ai_criteria_shadow_no_auto_pass",
            ),
        ),
        migrations.AddConstraint(
            model_name="aianalysisrun",
            constraint=models.CheckConstraint(
                condition=models.Q(("shadow_mode", True), ("auto_pass_activated", False)),
                name="ai_run_shadow_no_auto_pass",
            ),
        ),
    ]

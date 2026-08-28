"""C-13: Add server-side privacy decision fields to EvidenceItem.

The new columns are deliberately additive so the migration is safe in
production. The default value of ``privacy_decision`` is
``pending_review`` so the platform never claims an existing row was
authorised by the new pipeline.
"""

from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("evidence", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="evidenceitem",
            name="privacy_decision",
            field=models.CharField(
                choices=[
                    ("approved_blurred", "Approved blurred"),
                    ("retained_unblurred", "Retained unblurred"),
                    ("rejected_no_face", "Rejected - no face"),
                    ("pending_review", "Pending review"),
                    ("failed_detector", "Detector failed"),
                ],
                default="pending_review",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="evidenceitem",
            name="face_detector_version",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="evidenceitem",
            name="face_detector_confidence",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="evidenceitem",
            name="face_detector_raw_score",
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name="evidenceitem",
            name="privacy_metadata",
            field=models.JSONField(default=dict),
        ),
    ]

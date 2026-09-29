import pytest
from apps.tasks.serializers import TaskScheduleSerializer
from apps.tasks.models import TaskRecurrenceType

@pytest.mark.django_db
def test_task_schedule_serializer_validation():
    serializer = TaskScheduleSerializer(data={
        "recurrence_type": TaskRecurrenceType.DAILY_FIXED,
        "scheduled_time": None
    })
    assert not serializer.is_valid()
    assert "scheduled_time" in serializer.errors

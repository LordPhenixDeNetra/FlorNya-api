"""Unit tests for ReminderService."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.reminder import ReminderConfigCreate, ReminderType


@pytest.mark.anyio
async def test_reminder_type_values():
    assert ReminderType.period.value == "period"
    assert ReminderType.medication.value == "medication"
    assert ReminderType.hydration.value == "hydration"
    assert ReminderType.mood_checkin.value == "mood_checkin"


@pytest.mark.anyio
async def test_reminder_config_defaults():
    data = ReminderConfigCreate()
    assert data.is_enabled is True
    assert data.time_of_day == "20:00"
    assert data.label is None


@pytest.mark.anyio
async def test_reminder_config_time_validation():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ReminderConfigCreate(time_of_day="invalid")

    valid = ReminderConfigCreate(time_of_day="08:30")
    assert valid.time_of_day == "08:30"

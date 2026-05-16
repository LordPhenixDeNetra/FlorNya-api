"""Unit tests for CycleService (non-DB logic)."""
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.phase_calculator import PhaseCalculator


@pytest.mark.anyio
async def test_phase_calculator_cycle_day():
    calc = PhaseCalculator()
    start = date(2024, 1, 1)
    assert calc.calculate_cycle_day(start, date(2024, 1, 1)) == 1
    assert calc.calculate_cycle_day(start, date(2024, 1, 15)) == 15


@pytest.mark.anyio
async def test_phase_calculator_phases():
    calc = PhaseCalculator()
    from app.schemas.cycle import CyclePhase

    assert calc.calculate_phase(1, 28) == CyclePhase.menstrual
    assert calc.calculate_phase(10, 28) == CyclePhase.follicular
    assert calc.calculate_phase(14, 28) == CyclePhase.ovulatory
    assert calc.calculate_phase(20, 28) == CyclePhase.luteal


@pytest.mark.anyio
async def test_phase_calculator_fertile_window():
    calc = PhaseCalculator()
    start = date(2024, 1, 1)
    fw = calc.get_fertile_window(start, 28)
    assert fw.start <= fw.end
    assert (fw.end - fw.start).days <= 6


@pytest.mark.anyio
async def test_phase_calculator_next_period():
    calc = PhaseCalculator()
    start = date(2024, 1, 1)
    next_p = calc.predict_next_period(start, 28)
    assert next_p == start + timedelta(days=28)

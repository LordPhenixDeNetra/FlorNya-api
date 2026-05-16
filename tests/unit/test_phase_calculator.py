from datetime import date

from app.schemas.cycle import CyclePhase
from app.services.phase_calculator import PhaseCalculator


def test_phase_calculation_regular_cycle() -> None:
    calc = PhaseCalculator()
    last_period = date(2026, 5, 1)
    today = date(2026, 5, 14)
    cycle_day = calc.calculate_cycle_day(last_period, today)
    phase = calc.calculate_phase(cycle_day, 28)
    assert cycle_day == 14
    assert phase in {CyclePhase.ovulatory, CyclePhase.follicular}

from datetime import date, timedelta

from app.schemas.cycle import CyclePhase, FertileWindow


class PhaseCalculator:
    def calculate_cycle_day(self, last_period_start: date, today: date) -> int:
        return (today - last_period_start).days + 1

    def predict_next_period(self, last_period_start: date, cycle_length: int) -> date:
        return last_period_start + timedelta(days=cycle_length)

    def predict_ovulation(self, last_period_start: date, cycle_length: int) -> date:
        ovulation_day = max(10, cycle_length - 14)
        return last_period_start + timedelta(days=ovulation_day - 1)

    def get_fertile_window(self, last_period_start: date, cycle_length: int) -> FertileWindow:
        ovulation_date = self.predict_ovulation(last_period_start, cycle_length)
        return FertileWindow(start=ovulation_date - timedelta(days=5), end=ovulation_date + timedelta(days=1))

    def calculate_phase(self, cycle_day: int, cycle_length: int) -> CyclePhase:
        if cycle_day <= 5:
            return CyclePhase.menstrual
        ovulation_day = max(10, cycle_length - 14)
        if cycle_day < ovulation_day:
            return CyclePhase.follicular
        if cycle_day <= ovulation_day + 2:
            return CyclePhase.ovulatory
        return CyclePhase.luteal

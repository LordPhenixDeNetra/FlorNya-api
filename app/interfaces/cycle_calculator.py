from abc import ABC, abstractmethod
from datetime import date

from app.schemas.cycle import CyclePhase, FertileWindow


class ICycleCalculator(ABC):
    @abstractmethod
    def calculate_cycle_day(self, last_period_start: date, today: date) -> int: ...

    @abstractmethod
    def predict_next_period(self, last_period_start: date, cycle_length: int) -> date: ...

    @abstractmethod
    def predict_ovulation(self, last_period_start: date, cycle_length: int) -> date: ...

    @abstractmethod
    def get_fertile_window(self, last_period_start: date, cycle_length: int) -> FertileWindow: ...

    @abstractmethod
    def calculate_phase(self, cycle_day: int, cycle_length: int) -> CyclePhase: ...

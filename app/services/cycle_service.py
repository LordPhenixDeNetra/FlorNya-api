from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_sensitive, encrypt_sensitive
from app.models.user import User
from app.repositories.cycle_repository import CycleRepository
from app.schemas.common import PaginatedResponse
from app.schemas.cycle import CurrentCycleResponse, CycleFilterParams, CycleRecordCreate, CycleRecordPublic
from app.services.phase_calculator import PhaseCalculator


class CycleService:
    def __init__(self, session: AsyncSession, cycles: CycleRepository, calculator: PhaseCalculator):
        self.session = session
        self.cycles = cycles
        self.calculator = calculator

    async def create_record(self, user: User, data: CycleRecordCreate) -> CycleRecordPublic:
        entity = await self.cycles.create(
            user_id=user.id,
            period_start=data.period_start,
            cycle_length=data.cycle_length,
            notes_encrypted=encrypt_sensitive(data.notes),
        )
        await self.session.commit()
        await self.session.refresh(entity)
        return self._to_public(entity)

    async def list_records(self, user: User, params: CycleFilterParams) -> PaginatedResponse[CycleRecordPublic]:
        items, total = await self.cycles.list(
            user_id=user.id,
            date_from=params.date_from,
            date_to=params.date_to,
            skip=params.skip,
            limit=params.limit,
            sort_by=params.sort_by,
            order=params.order.value,
        )
        public_items = [self._to_public(x) for x in items]
        has_more = params.skip + len(public_items) < total
        return PaginatedResponse(
            items=public_items,
            total=total,
            skip=params.skip,
            limit=params.limit,
            has_more=has_more,
        )

    async def get_current(self, user: User, today: date | None = None) -> CurrentCycleResponse:
        today = today or date.today()
        latest = await self.cycles.get_latest(user.id)
        if latest is None:
            raise ValueError("no_cycle_data")

        last_period_start = latest.period_start
        cycle_length = latest.cycle_length

        if today > last_period_start + timedelta(days=cycle_length):
            days_since = (today - last_period_start).days
            cycles_passed = days_since // cycle_length
            last_period_start = last_period_start + timedelta(days=cycles_passed * cycle_length)

        cycle_day = self.calculator.calculate_cycle_day(last_period_start, today)
        phase = self.calculator.calculate_phase(cycle_day, cycle_length)
        next_period = self.calculator.predict_next_period(last_period_start, cycle_length)
        fertile_window = self.calculator.get_fertile_window(last_period_start, cycle_length)
        return CurrentCycleResponse(
            phase=phase,
            cycle_day=cycle_day,
            last_period_start=last_period_start,
            next_period_predicted=next_period,
            fertile_window=fertile_window,
        )

    def _to_public(self, entity) -> CycleRecordPublic:
        return CycleRecordPublic(
            id=entity.id,
            user_id=entity.user_id,
            period_start=entity.period_start,
            cycle_length=entity.cycle_length,
            notes=decrypt_sensitive(entity.notes_encrypted),
            created_at=entity.created_at,
        )

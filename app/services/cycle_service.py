import calendar as cal_module
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_sensitive, encrypt_sensitive
from app.models.cycle_record import FlowIntensity as FlowIntensityModel
from app.models.user import User
from app.repositories.cycle_repository import CycleRepository
from app.repositories.mood_repository import MoodRepository
from app.repositories.symptom_repository import SymptomRepository
from app.schemas.common import PaginatedResponse
from app.schemas.cycle import (
    CalendarDay,
    CalendarResponse,
    CurrentCycleResponse,
    CycleFilterParams,
    CycleInsightsResponse,
    CyclePhase,
    CycleRecordCreate,
    CycleRecordPublic,
    FertileWindow,
    FlowIntensity,
    SymptomFilterParams,
    SymptomLogCreate,
    SymptomLogPublic,
)
from app.services.phase_calculator import PhaseCalculator


class CycleService:
    def __init__(
        self,
        session: AsyncSession,
        cycles: CycleRepository,
        calculator: PhaseCalculator,
        symptoms: SymptomRepository | None = None,
        moods: MoodRepository | None = None,
        ai_service: object | None = None,
    ):
        self.session = session
        self.cycles = cycles
        self.calculator = calculator
        self.symptoms = symptoms
        self.moods = moods
        self.ai_service = ai_service

    # ── Cycle records ─────────────────────────────────────────────────────

    async def create_record(self, user: User, data: CycleRecordCreate) -> CycleRecordPublic:
        flow = FlowIntensityModel(data.flow_intensity.value) if data.flow_intensity else None
        entity = await self.cycles.create(
            user_id=user.id,
            period_start=data.period_start,
            period_end=data.period_end,
            cycle_length=data.cycle_length,
            flow_intensity=flow,
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

    # ── Calendar ──────────────────────────────────────────────────────────

    async def get_calendar(self, user: User, year: int, month: int) -> CalendarResponse:
        _, days_in_month = cal_module.monthrange(year, month)
        month_start = date(year, month, 1)
        month_end = date(year, month, days_in_month)

        # Fetch the most recent cycle record at or before the month start
        latest = await self.cycles.get_latest(user.id)

        # All dates in the month
        all_dates = [date(year, month, d) for d in range(1, days_in_month + 1)]

        # Dates with symptoms and moods
        symptom_dates: set[date] = set()
        mood_dates: set[date] = set()

        if self.symptoms:
            symptom_dates = await self.symptoms.get_dates_with_symptoms(user.id, all_dates)

        if self.moods:
            items, _, _ = await self.moods.list_cursor(
                user_id=user.id,
                date_from=month_start,
                min_score=None,
                cursor=None,
                limit=100,
            )
            mood_dates = {m.log_date for m in items}

        calendar_days: list[CalendarDay] = []

        for d in all_dates:
            phase: CyclePhase | None = None
            cycle_day: int | None = None
            is_period = False
            is_fertile = False

            if latest is not None:
                last_start = latest.period_start
                cycle_len = latest.cycle_length

                # Project last period start forward to the nearest cycle start before or on d
                if d >= last_start:
                    days_since = (d - last_start).days
                    cycles_elapsed = days_since // cycle_len
                    projected_start = last_start + timedelta(days=cycles_elapsed * cycle_len)
                    cday = self.calculator.calculate_cycle_day(projected_start, d)
                    phase = self.calculator.calculate_phase(cday, cycle_len)
                    cycle_day = cday

                    # is_period: first N days of menstrual phase (use period_length from profile or default 5)
                    is_period = phase == CyclePhase.menstrual

                    # Fertile window
                    fw = self.calculator.get_fertile_window(projected_start, cycle_len)
                    is_fertile = fw.start <= d <= fw.end

            calendar_days.append(
                CalendarDay(
                    date=d,
                    phase=phase,
                    cycle_day=cycle_day,
                    is_period=is_period,
                    is_fertile=is_fertile,
                    has_symptoms=d in symptom_dates,
                    has_mood=d in mood_dates,
                )
            )

        return CalendarResponse(year=year, month=month, days=calendar_days)

    # ── Symptom logs ──────────────────────────────────────────────────────

    async def log_symptoms(self, user: User, data: SymptomLogCreate) -> SymptomLogPublic:
        if self.symptoms is None:
            raise RuntimeError("symptoms repository not configured")

        entity = await self.symptoms.upsert(
            user_id=user.id,
            log_date=data.log_date,
            cramps=data.cramps,
            bloating=data.bloating,
            breast_tenderness=data.breast_tenderness,
            headache=data.headache,
            acne=data.acne,
            fatigue=data.fatigue,
            energy=data.energy,
            sleep_quality=data.sleep_quality,
            libido=data.libido,
            intensity=data.intensity,
            notes_encrypted=encrypt_sensitive(data.notes),
        )
        await self.session.commit()
        await self.session.refresh(entity)
        return self._symptom_to_public(entity)

    async def list_symptoms(self, user: User, params: SymptomFilterParams) -> list[SymptomLogPublic]:
        if self.symptoms is None:
            return []
        items = await self.symptoms.list_range(
            user_id=user.id, date_from=params.date_from, date_to=params.date_to
        )
        return [self._symptom_to_public(s) for s in items]

    # ── AI Insights (Bloom) ───────────────────────────────────────────────

    async def get_insights(self, user: User) -> CycleInsightsResponse:
        items, _ = await self.cycles.list(
            user_id=user.id, date_from=None, date_to=None,
            skip=0, limit=12, sort_by="period_start", order="desc"
        )

        cycle_lengths = [r.cycle_length for r in items]
        regularity_score: float | None = None
        if len(cycle_lengths) >= 3:
            avg = sum(cycle_lengths) / len(cycle_lengths)
            variance = sum((l - avg) ** 2 for l in cycle_lengths) / len(cycle_lengths)
            regularity_score = round(max(0.0, 1.0 - (variance / 100)), 2)

        dominant_symptoms: list[str] = []
        if self.symptoms:
            symptom_items = await self.symptoms.list_range(
                user_id=user.id,
                date_from=(date.today() - timedelta(days=90)),
                date_to=date.today(),
            )
            counts: dict[str, int] = {}
            for s in symptom_items:
                for field in ("cramps", "bloating", "breast_tenderness", "headache", "acne", "fatigue"):
                    if getattr(s, field, False):
                        counts[field] = counts.get(field, 0) + 1
            dominant_symptoms = sorted(counts, key=lambda k: counts[k], reverse=True)[:3]

        insights_md = "**Analyse de votre cycle**\n\nVos données de cycle ont été analysées."

        if self.ai_service is not None:
            context = {
                "cycle_count": len(items),
                "avg_cycle_length": sum(cycle_lengths) / len(cycle_lengths) if cycle_lengths else None,
                "regularity_score": regularity_score,
                "dominant_symptoms": dominant_symptoms,
                "language": user.language,
            }
            try:
                insights_md = await self.ai_service.generate_cycle_insights(context)
            except Exception:
                pass

        return CycleInsightsResponse(
            generated_at=datetime.now(timezone.utc),
            insights_markdown=insights_md,
            cycle_regularity_score=regularity_score,
            dominant_symptoms=dominant_symptoms,
        )

    # ── PDF export (Bloom Pro) ─────────────────────────────────────────────

    async def export_pdf(self, user: User) -> bytes:
        from datetime import timedelta
        from jinja2 import Environment, FileSystemLoader
        from pathlib import Path
        import weasyprint

        items, _ = await self.cycles.list(
            user_id=user.id,
            date_from=date.today() - timedelta(days=180),
            date_to=date.today(),
            skip=0, limit=100,
            sort_by="period_start", order="desc"
        )
        records = [
            {
                "period_start": str(r.period_start),
                "period_end": str(r.period_end) if r.period_end else "–",
                "cycle_length": r.cycle_length,
                "flow_intensity": r.flow_intensity.value if r.flow_intensity else "–",
                "notes": decrypt_sensitive(r.notes_encrypted) or "",
            }
            for r in items
        ]

        template_dir = Path(__file__).parent.parent / "templates" / "pdf"
        env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)
        tmpl = env.get_template("cycle_report.html")
        html_str = tmpl.render(
            user_name=user.first_name or user.email,
            records=records,
            generated_at=datetime.now(timezone.utc).strftime("%d/%m/%Y"),
        )
        return weasyprint.HTML(string=html_str, base_url=template_dir.as_uri() + "/").write_pdf()

    # ── Private helpers ───────────────────────────────────────────────────

    def _to_public(self, entity: object) -> CycleRecordPublic:
        fi = getattr(entity, "flow_intensity", None)
        return CycleRecordPublic(
            id=entity.id,  # type: ignore[attr-defined]
            user_id=entity.user_id,  # type: ignore[attr-defined]
            period_start=entity.period_start,  # type: ignore[attr-defined]
            period_end=getattr(entity, "period_end", None),
            cycle_length=entity.cycle_length,  # type: ignore[attr-defined]
            flow_intensity=FlowIntensity(fi.value) if fi else None,
            notes=decrypt_sensitive(entity.notes_encrypted),  # type: ignore[attr-defined]
            created_at=entity.created_at,  # type: ignore[attr-defined]
        )

    def _symptom_to_public(self, entity: object) -> SymptomLogPublic:
        return SymptomLogPublic(
            id=entity.id,  # type: ignore[attr-defined]
            user_id=entity.user_id,  # type: ignore[attr-defined]
            log_date=entity.log_date,  # type: ignore[attr-defined]
            cramps=entity.cramps,  # type: ignore[attr-defined]
            bloating=entity.bloating,  # type: ignore[attr-defined]
            breast_tenderness=entity.breast_tenderness,  # type: ignore[attr-defined]
            headache=entity.headache,  # type: ignore[attr-defined]
            acne=entity.acne,  # type: ignore[attr-defined]
            fatigue=entity.fatigue,  # type: ignore[attr-defined]
            energy=entity.energy,  # type: ignore[attr-defined]
            sleep_quality=entity.sleep_quality,  # type: ignore[attr-defined]
            libido=entity.libido,  # type: ignore[attr-defined]
            intensity=entity.intensity,  # type: ignore[attr-defined]
            notes=decrypt_sensitive(entity.notes_encrypted),  # type: ignore[attr-defined]
            created_at=entity.created_at,  # type: ignore[attr-defined]
        )

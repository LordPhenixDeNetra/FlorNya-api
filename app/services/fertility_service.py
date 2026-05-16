import json
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_sensitive, encrypt_sensitive
from app.models.conception_attempt import ConceptionAttempt
from app.models.fertility_log import CervicalMucusType, FertilityLog, LHTestResult
from app.models.user import User
from app.repositories.fertility_repository import ConceptionAttemptRepository, FertilityRepository
from app.schemas.fertility import (
    ConceptionAttemptCreate,
    ConceptionAttemptPublic,
    CervicalMucusType as MucusSchema,
    FertilityCoachResponse,
    FertilityLogCreate,
    FertilityLogPublic,
    FertilityScoreResponse,
    LHTestResult as LHSchema,
)
from app.services.phase_calculator import PhaseCalculator


_MUCUS_FERTILITY_SCORE = {
    CervicalMucusType.egg_white: 30,
    CervicalMucusType.watery: 20,
    CervicalMucusType.creamy: 5,
    CervicalMucusType.dry: 0,
}

_LH_FERTILITY_SCORE = {
    LHTestResult.peak: 40,
    LHTestResult.positive: 30,
    LHTestResult.negative: 0,
}


class FertilityService:
    def __init__(
        self,
        session: AsyncSession,
        fertility_repo: FertilityRepository,
        conception_repo: ConceptionAttemptRepository,
        calculator: PhaseCalculator,
        ai_service: object | None = None,
    ):
        self.session = session
        self.fertility_repo = fertility_repo
        self.conception_repo = conception_repo
        self.calculator = calculator
        self.ai_service = ai_service

    # ── Fertility log ─────────────────────────────────────────────────────

    async def log_fertility(self, user: User, data: FertilityLogCreate) -> FertilityLogPublic:
        mucus = CervicalMucusType(data.cervical_mucus.value) if data.cervical_mucus else None
        lh = LHTestResult(data.lh_test_result.value) if data.lh_test_result else None
        entity = await self.fertility_repo.upsert(
            user_id=user.id,
            log_date=data.log_date,
            bbt_celsius=data.bbt_celsius,
            cervical_mucus=mucus,
            lh_test_result=lh,
            notes_encrypted=encrypt_sensitive(data.notes),
        )
        await self.session.commit()
        await self.session.refresh(entity)
        return self._to_public(entity)

    async def list_fertility_logs(
        self, user: User, date_from: date | None = None, date_to: date | None = None
    ) -> list[FertilityLogPublic]:
        items = await self.fertility_repo.list_range(
            user_id=user.id, date_from=date_from, date_to=date_to
        )
        return [self._to_public(e) for e in items]

    # ── Fertility score ───────────────────────────────────────────────────

    async def get_fertility_score(
        self, user: User, target_date: date, cycle_start: date, cycle_length: int
    ) -> FertilityScoreResponse:
        cycle_day = self.calculator.calculate_cycle_day(cycle_start, target_date)
        fw = self.calculator.get_fertile_window(cycle_start, cycle_length)

        ovulation_day = cycle_length - 14
        days_to_ovulation = abs(cycle_day - ovulation_day)

        base_score = max(0.0, 50.0 - (days_to_ovulation * 10))

        log = await self.fertility_repo.get_by_user_date(user.id, target_date)
        if log:
            if log.cervical_mucus:
                base_score += _MUCUS_FERTILITY_SCORE.get(log.cervical_mucus, 0)
            if log.lh_test_result:
                base_score += _LH_FERTILITY_SCORE.get(log.lh_test_result, 0)

        score = min(100.0, max(0.0, base_score))
        is_fertile = fw.start <= target_date <= fw.end
        ovulation_predicted = cycle_day == ovulation_day

        if score >= 70:
            details = "Fenêtre fertile optimale — moment idéal pour tenter une conception."
        elif score >= 40:
            details = "Fertilité modérée — période potentiellement fertile."
        else:
            details = "Fertilité faible — hors fenêtre fertile estimée."

        return FertilityScoreResponse(
            date=target_date,
            score=round(score, 1),
            fertile=is_fertile,
            ovulation_predicted=ovulation_predicted,
            details=details,
        )

    # ── Conception attempts ───────────────────────────────────────────────

    async def log_attempt(self, user: User, data: ConceptionAttemptCreate) -> ConceptionAttemptPublic:
        entity = ConceptionAttempt(
            user_id=user.id,
            attempt_date=data.attempt_date,
            notes_encrypted=encrypt_sensitive(data.notes),
        )
        await self.conception_repo.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return ConceptionAttemptPublic(
            id=entity.id,
            user_id=entity.user_id,
            attempt_date=entity.attempt_date,
            notes=decrypt_sensitive(entity.notes_encrypted),
            created_at=entity.created_at,
        )

    async def list_attempts(self, user: User) -> list[ConceptionAttemptPublic]:
        items = await self.conception_repo.list_by_user(user.id)
        return [
            ConceptionAttemptPublic(
                id=e.id,
                user_id=e.user_id,
                attempt_date=e.attempt_date,
                notes=decrypt_sensitive(e.notes_encrypted),
                created_at=e.created_at,
            )
            for e in items
        ]

    # ── AI Fertility coach ────────────────────────────────────────────────

    async def fertility_coach(self, user: User, question: str, cycle_context: dict) -> FertilityCoachResponse:
        answer = "Je suis là pour vous accompagner dans votre parcours de conception."
        if self.ai_service is not None:
            try:
                context = {**cycle_context, "language": user.language}
                answer = await self.ai_service.fertility_coach(question, context)
            except Exception:
                pass
        return FertilityCoachResponse(answer=answer)

    # ── Private helpers ───────────────────────────────────────────────────

    def _to_public(self, entity: FertilityLog) -> FertilityLogPublic:
        mucus = MucusSchema(entity.cervical_mucus.value) if entity.cervical_mucus else None
        lh = LHSchema(entity.lh_test_result.value) if entity.lh_test_result else None
        return FertilityLogPublic(
            id=entity.id,
            user_id=entity.user_id,
            log_date=entity.log_date,
            bbt_celsius=entity.bbt_celsius,
            cervical_mucus=mucus,
            lh_test_result=lh,
            notes=decrypt_sensitive(entity.notes_encrypted),
            created_at=entity.created_at,
        )

from datetime import date, timedelta, datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_sensitive, encrypt_sensitive
from app.models.emotional_journal import EmotionalJournalEntry, JournalPromptType
from app.models.mental_alert import MentalAlert, MentalAlertType
from app.models.user import User
from app.repositories.emotional_journal_repository import EmotionalJournalRepository
from app.repositories.mental_alert_repository import MentalAlertRepository
from app.repositories.mood_repository import MoodRepository
from app.schemas.common import CursorPaginatedResponse
from app.schemas.mental import (
    EmotionalJournalCreate,
    EmotionalJournalPublic,
    MentalAlertPublic,
    MentalInsightsResponse,
    MentalResourcePublic,
    MoodCorrelationResponse,
    MoodFilterParams,
    MoodLogCreate,
    MoodLogPublic,
    MoodPhaseCorrelation,
    SPMDetectionResult,
    StressTechniquePublic,
)
from app.services.ai.anthropic_service import AnthropicInsightService


def _period_to_timedelta(period: str) -> timedelta:
    value = int(period[:-1])
    unit = period[-1]
    if unit == "d":
        return timedelta(days=value)
    if unit == "w":
        return timedelta(weeks=value)
    if unit == "m":
        return timedelta(days=value * 30)
    raise ValueError("invalid_period")


_STRESS_TECHNIQUES = [
    StressTechniquePublic(
        id="box_breathing",
        name="Respiration en carré",
        description="Technique de cohérence cardiaque pour réduire le cortisol",
        duration_minutes=5,
        phase_recommended="luteal",
        category="breathing",
        steps=["Inspire 4 secondes", "Retiens 4 secondes", "Expire 4 secondes", "Retiens 4 secondes", "Répète 4 fois"],
    ),
    StressTechniquePublic(
        id="478_breathing",
        name="Respiration 4-7-8",
        description="Active le système parasympathique pour calmer l'anxiété",
        duration_minutes=3,
        phase_recommended=None,
        category="breathing",
        steps=["Expire complètement", "Inspire 4 secondes", "Retiens 7 secondes", "Expire 8 secondes", "Répète 3 fois"],
    ),
    StressTechniquePublic(
        id="body_scan",
        name="Scan corporel",
        description="Méditation de pleine conscience pour relâcher les tensions",
        duration_minutes=10,
        phase_recommended="menstrual",
        category="meditation",
        steps=["Allonge-toi confortablement", "Ferme les yeux", "Scanne chaque partie du corps", "Relâche les tensions", "Observe sans juger"],
    ),
    StressTechniquePublic(
        id="gratitude_journal",
        name="Journal de gratitude",
        description="Recadrage cognitif positif pour améliorer l'humeur",
        duration_minutes=5,
        phase_recommended=None,
        category="journaling",
        steps=["Note 3 choses positives du jour", "Explique pourquoi tu es reconnaissante", "Lis-les à voix haute", "Ressens la gratitude"],
    ),
    StressTechniquePublic(
        id="progressive_relaxation",
        name="Relaxation musculaire progressive",
        description="Contracte et relâche chaque groupe musculaire",
        duration_minutes=15,
        phase_recommended="premenstrual",
        category="relaxation",
        steps=["Commence par les pieds", "Contracte 5 secondes", "Relâche complètement", "Remonte vers la tête", "Sens la détente"],
    ),
]

_MENTAL_RESOURCES = [
    MentalResourcePublic(
        category="urgence",
        title="Numéro national de prévention du suicide",
        description="Ligne d'écoute disponible 24h/24, 7j/7",
        url=None,
        phone="3114",
        country="FR",
    ),
    MentalResourcePublic(
        category="soutien",
        title="SOS Amitié",
        description="Écoute et soutien émotionnel anonyme",
        url="https://www.sos-amitie.com",
        phone="09 72 39 40 50",
        country="FR",
    ),
    MentalResourcePublic(
        category="professionnel",
        title="Trouver un psychologue",
        description="Annuaire des psychologues spécialisés en santé féminine",
        url="https://www.doctolib.fr/psychologue",
        phone=None,
        country="FR",
    ),
    MentalResourcePublic(
        category="self_help",
        title="FlorNya Bien-être",
        description="Techniques de gestion du stress dans l'application",
        url=None,
        phone=None,
        country=None,
    ),
]


class MentalService:
    def __init__(
        self,
        session: AsyncSession,
        moods: MoodRepository,
        journals: EmotionalJournalRepository | None = None,
        alerts: MentalAlertRepository | None = None,
        ai_service: AnthropicInsightService | None = None,
    ):
        self.session = session
        self.moods = moods
        self.journals = journals
        self.alerts = alerts
        self.ai_service = ai_service

    async def create_mood(self, user: User, data: MoodLogCreate) -> MoodLogPublic:
        entity = await self.moods.create(
            user_id=user.id,
            log_date=data.log_date,
            mood_score=data.mood_score,
            journal_text_encrypted=encrypt_sensitive(data.journal_text),
        )
        await self.session.commit()
        await self.session.refresh(entity)

        # Check distress alert (score <= 2 for 3 consecutive days)
        await self._check_distress_alert(user)

        return self._to_public(entity)

    async def list_moods(self, user: User, params: MoodFilterParams) -> CursorPaginatedResponse[MoodLogPublic]:
        date_from = None
        if params.period:
            date_from = date.today() - _period_to_timedelta(params.period)

        items, next_cursor, has_more = await self.moods.list_cursor(
            user_id=user.id,
            date_from=date_from,
            min_score=params.min_score,
            cursor=params.cursor,
            limit=params.limit,
        )
        public_items = [self._to_public(x) for x in items]
        return CursorPaginatedResponse(items=public_items, next_cursor=next_cursor, has_more=has_more)

    # ── Emotional Journal ─────────────────────────────────────────────────

    async def add_journal_entry(self, user: User, data: EmotionalJournalCreate) -> EmotionalJournalPublic:
        if self.journals is None:
            raise ValueError("journal_repository_not_initialized")

        prompt_text: str | None = None
        if data.prompt_type == "ai_generated" and self.ai_service:
            from app.services.phase_calculator import PhaseCalculator
            prompt_text = await self.ai_service.generate_journal_prompt(
                mood_score=data.mood_score_at_entry or 3,
                cycle_phase="follicular",
                language=user.language,
            )

        entry = await self.journals.create(
            user_id=user.id,
            log_date=data.log_date,
            text_encrypted=encrypt_sensitive(data.text),
            prompt_type=JournalPromptType(data.prompt_type),
            prompt_text_encrypted=encrypt_sensitive(prompt_text),
            mood_score_at_entry=data.mood_score_at_entry,
        )
        await self.session.commit()
        await self.session.refresh(entry)
        return self._journal_to_public(entry)

    async def list_journal_entries(self, user: User, limit: int = 30, offset: int = 0) -> list[EmotionalJournalPublic]:
        if self.journals is None:
            return []
        entries = await self.journals.list_by_user(user.id, limit=limit, offset=offset)
        return [self._journal_to_public(e) for e in entries]

    async def get_ai_journal_prompt(self, user: User, mood_score: int, cycle_phase: str = "follicular") -> str:
        if not self.ai_service:
            return "Comment te sens-tu aujourd'hui ? Qu'est-ce qui t'a le plus marquée ?"
        return await self.ai_service.generate_journal_prompt(
            mood_score=mood_score, cycle_phase=cycle_phase, language=user.language
        )

    # ── Stress Techniques ─────────────────────────────────────────────────

    def get_stress_techniques(self, phase: str | None = None) -> list[StressTechniquePublic]:
        if phase:
            return [t for t in _STRESS_TECHNIQUES if t.phase_recommended is None or t.phase_recommended == phase]
        return _STRESS_TECHNIQUES

    # ── Mood Correlation ──────────────────────────────────────────────────

    async def get_mood_correlation(self, user: User) -> MoodCorrelationResponse:
        from sqlalchemy import select, func, and_
        from app.models.mood_log import MoodLog
        from app.models.cycle_record import CycleRecord

        cutoff = date.today() - timedelta(days=90)

        result = await self.session.execute(
            select(MoodLog.log_date, MoodLog.mood_score)
            .where(MoodLog.user_id == user.id, MoodLog.log_date >= cutoff)
            .order_by(MoodLog.log_date)
        )
        mood_rows = result.all()

        result2 = await self.session.execute(
            select(CycleRecord).where(CycleRecord.user_id == user.id).order_by(CycleRecord.period_start.desc()).limit(5)
        )
        cycles = list(result2.scalars().all())

        phase_scores: dict[str, list[int]] = {"menstrual": [], "follicular": [], "ovulatory": [], "luteal": []}

        for log_date, mood_score in mood_rows:
            phase = self._infer_phase(log_date, cycles)
            if phase in phase_scores:
                phase_scores[phase].append(mood_score)

        correlations = []
        for phase, scores in phase_scores.items():
            if scores:
                correlations.append(MoodPhaseCorrelation(
                    phase=phase,
                    average_mood=round(sum(scores) / len(scores), 2),
                    entries_count=len(scores),
                ))

        best = max(correlations, key=lambda x: x.average_mood, default=None)
        worst = min(correlations, key=lambda x: x.average_mood, default=None)

        insights = None
        if self.ai_service and correlations:
            insights = f"Votre humeur est meilleure en phase {best.phase if best else 'inconnue'}."

        return MoodCorrelationResponse(
            period_days=90,
            correlations=correlations,
            best_phase=best.phase if best else None,
            worst_phase=worst.phase if worst else None,
            insights=insights,
        )

    def _infer_phase(self, log_date: date, cycles: list) -> str:
        if not cycles:
            return "follicular"
        latest = cycles[0]
        cycle_day = (log_date - latest.period_start).days % (latest.cycle_length or 28) + 1
        if cycle_day <= 5:
            return "menstrual"
        if cycle_day <= 13:
            return "follicular"
        if cycle_day <= 16:
            return "ovulatory"
        return "luteal"

    # ── SPM Detection ─────────────────────────────────────────────────────

    async def detect_spm(self, user: User) -> SPMDetectionResult:
        cutoff = date.today() - timedelta(days=60)

        from sqlalchemy import select
        from app.models.mood_log import MoodLog
        from app.models.symptom_log import SymptomLog

        mood_result = await self.session.execute(
            select(MoodLog.log_date, MoodLog.mood_score)
            .where(MoodLog.user_id == user.id, MoodLog.log_date >= cutoff)
            .order_by(MoodLog.log_date)
        )
        mood_data = [{"date": str(r.log_date), "score": r.mood_score} for r in mood_result.all()]

        sym_result = await self.session.execute(
            select(SymptomLog)
            .where(SymptomLog.user_id == user.id, SymptomLog.log_date >= cutoff)
            .order_by(SymptomLog.log_date)
        )
        symptom_data = [
            {"date": str(s.log_date), "cramps": s.cramps, "bloating": s.bloating, "fatigue": s.fatigue}
            for s in sym_result.scalars().all()
        ]

        low_score_days = [d for d in mood_data if d["score"] <= 2]
        detected = len(low_score_days) >= 5

        recommendations = [
            "Suivre l'humeur quotidiennement",
            "Consommer des aliments riches en magnésium (Phase lutéale)",
            "Pratiquer des exercices doux comme le yoga",
            "Consulter un gynécologue si les symptômes impactent la vie quotidienne",
        ]

        if detected and self.ai_service:
            ai_result = await self.ai_service.detect_spm_pattern(mood_data, symptom_data, user.language)
            severity = "modérée" if "modérée" in ai_result.lower() else ("sévère" if "sévère" in ai_result.lower() else "légère")
        else:
            severity = "non détecté" if not detected else "légère"

        return SPMDetectionResult(
            detected=detected,
            severity=severity,
            pattern_days=len(low_score_days),
            symptoms_correlation=["humeur basse", "crampes", "fatigue"] if detected else [],
            recommendations=recommendations if detected else [],
            alert_level="attention" if detected else "normal",
        )

    # ── Emotional Insights ────────────────────────────────────────────────

    async def get_emotional_insights(self, user: User) -> MentalInsightsResponse:
        cutoff = date.today() - timedelta(days=30)
        from sqlalchemy import select
        from app.models.mood_log import MoodLog

        result = await self.session.execute(
            select(MoodLog.mood_score, MoodLog.log_date)
            .where(MoodLog.user_id == user.id, MoodLog.log_date >= cutoff)
            .order_by(MoodLog.log_date)
        )
        rows = result.all()

        if not rows:
            return MentalInsightsResponse(
                generated_at=datetime.now(timezone.utc),
                insights_markdown="Pas assez de données. Commencez à enregistrer votre humeur quotidiennement.",
                average_mood_score=None,
                mood_trend="stable",
                distress_days_detected=0,
                recommendations=["Enregistrez votre humeur chaque jour"],
            )

        scores = [r.mood_score for r in rows]
        avg = sum(scores) / len(scores)
        distress_days = sum(1 for s in scores if s <= 2)

        if len(scores) >= 7:
            recent_avg = sum(scores[-7:]) / 7
            older_avg = sum(scores[:-7]) / max(len(scores) - 7, 1)
            trend = "improving" if recent_avg > older_avg + 0.3 else ("declining" if recent_avg < older_avg - 0.3 else "stable")
        else:
            trend = "stable"

        insights_md = f"## Analyse émotionnelle du mois\n\n**Score moyen:** {avg:.1f}/5\n**Tendance:** {trend}\n**Jours difficiles:** {distress_days}"

        if self.ai_service:
            ai_text = await self.ai_service.generate_emotional_insights({
                "language": user.language,
                "average_mood_score": avg,
                "distress_days": distress_days,
                "cycle_phase": "follicular",
            })
            insights_md = ai_text

        recommendations = [
            "Continuez à enregistrer votre humeur quotidiennement",
            "Essayez les techniques de respiration en phase lutéale",
        ]
        if distress_days >= 3:
            recommendations.insert(0, "Consultez un professionnel de santé mentale si besoin")

        return MentalInsightsResponse(
            generated_at=datetime.now(timezone.utc),
            insights_markdown=insights_md,
            average_mood_score=round(avg, 2),
            mood_trend=trend,
            distress_days_detected=distress_days,
            recommendations=recommendations,
        )

    # ── Mental Alerts ─────────────────────────────────────────────────────

    async def get_mental_alerts(self, user: User) -> list[MentalAlertPublic]:
        if self.alerts is None:
            return []
        alerts = await self.alerts.list_unresolved(user.id)
        return [MentalAlertPublic(
            id=a.id, alert_type=a.alert_type.value, is_resolved=a.is_resolved,
            resources_sent=a.resources_sent, created_at=a.created_at,
        ) for a in alerts]

    async def resolve_alert(self, user: User, alert_id: UUID) -> None:
        if self.alerts is None:
            return
        from sqlalchemy import select
        result = await self.session.execute(
            select(MentalAlert).where(MentalAlert.id == alert_id, MentalAlert.user_id == user.id)
        )
        alert = result.scalar_one_or_none()
        if alert:
            alert.is_resolved = True
            alert.resolved_at = datetime.now(timezone.utc)
            await self.session.commit()

    # ── Resources ─────────────────────────────────────────────────────────

    def get_mental_resources(self) -> list[MentalResourcePublic]:
        return _MENTAL_RESOURCES

    # ── Private helpers ───────────────────────────────────────────────────

    async def _check_distress_alert(self, user: User) -> None:
        if self.alerts is None:
            return
        from sqlalchemy import select, and_
        from app.models.mood_log import MoodLog

        cutoff = date.today() - timedelta(days=3)
        result = await self.session.execute(
            select(MoodLog.mood_score)
            .where(and_(MoodLog.user_id == user.id, MoodLog.log_date >= cutoff))
            .order_by(MoodLog.log_date.desc())
            .limit(3)
        )
        recent_scores = [r for r in result.scalars().all()]

        if len(recent_scores) >= 3 and all(s <= 2 for s in recent_scores):
            existing = await self.alerts.get_latest(user.id, MentalAlertType.distress)
            if existing is None or existing.is_resolved:
                await self.alerts.create(user.id, MentalAlertType.distress)
                await self.session.commit()

    def _to_public(self, entity) -> MoodLogPublic:
        return MoodLogPublic(
            id=entity.id,
            user_id=entity.user_id,
            log_date=entity.log_date,
            mood_score=entity.mood_score,
            journal_text=decrypt_sensitive(entity.journal_text_encrypted),
            created_at=entity.created_at,
        )

    def _journal_to_public(self, entry: EmotionalJournalEntry) -> EmotionalJournalPublic:
        return EmotionalJournalPublic(
            id=entry.id,
            user_id=entry.user_id,
            log_date=entry.log_date,
            prompt_type=entry.prompt_type.value,
            prompt_text=decrypt_sensitive(entry.prompt_text_encrypted),
            text=decrypt_sensitive(entry.text_encrypted),
            mood_score_at_entry=entry.mood_score_at_entry,
            created_at=entry.created_at,
        )

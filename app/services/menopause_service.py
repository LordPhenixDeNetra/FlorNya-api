from datetime import date, datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_sensitive, encrypt_sensitive
from app.models.menopause_log import MenopauseLog
from app.models.user import User
from app.repositories.menopause_repository import MenopauseRepository
from app.schemas.menopause import (
    HotFlashQuickLog,
    MenopauseInsightsResponse,
    MenopauseLogCreate,
    MenopauseLogPublic,
    PerimenopauseScreening,
    PerimenopauseScreeningResult,
)


class MenopauseService:
    def __init__(
        self,
        session: AsyncSession,
        menopause_repo: MenopauseRepository,
        ai_service: object | None = None,
    ):
        self.session = session
        self.menopause_repo = menopause_repo
        self.ai_service = ai_service

    # ── Menopause log ─────────────────────────────────────────────────────

    async def log_symptoms(self, user: User, data: MenopauseLogCreate) -> MenopauseLogPublic:
        entity = await self.menopause_repo.upsert(
            user_id=user.id,
            log_date=data.log_date,
            hot_flash_count=data.hot_flash_count,
            night_sweats=data.night_sweats,
            vaginal_dryness=data.vaginal_dryness,
            insomnia=data.insomnia,
            mood_swings=data.mood_swings,
            weight_gain=data.weight_gain,
            brain_fog=data.brain_fog,
            joint_pain=data.joint_pain,
            severity=data.severity,
            notes_encrypted=encrypt_sensitive(data.notes),
        )
        await self.session.commit()
        await self.session.refresh(entity)
        return self._to_public(entity)

    async def quick_hot_flash(self, user: User, data: HotFlashQuickLog) -> MenopauseLogPublic:
        existing = await self.menopause_repo.get_by_user_date(user.id, data.log_date)
        if existing is not None:
            existing.hot_flash_count = (existing.hot_flash_count or 0) + data.count
            await self.session.flush()
            entity = existing
        else:
            entity = MenopauseLog(
                user_id=user.id,
                log_date=data.log_date,
                hot_flash_count=data.count,
            )
            await self.menopause_repo.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return self._to_public(entity)

    async def list_logs(
        self, user: User, date_from: date | None = None, date_to: date | None = None
    ) -> list[MenopauseLogPublic]:
        items = await self.menopause_repo.list_range(
            user_id=user.id, date_from=date_from, date_to=date_to
        )
        return [self._to_public(e) for e in items]

    # ── Insights ──────────────────────────────────────────────────────────

    async def get_insights(self, user: User) -> MenopauseInsightsResponse:
        avg_hf = await self.menopause_repo.avg_hot_flash_per_day(user.id, days=30)

        cutoff = date.today() - timedelta(days=30)
        items = await self.menopause_repo.list_range(
            user_id=user.id, date_from=cutoff, date_to=date.today()
        )

        symptom_counts: dict[str, int] = {}
        bool_fields = [
            "night_sweats", "vaginal_dryness", "insomnia",
            "mood_swings", "weight_gain", "brain_fog", "joint_pain",
        ]
        for item in items:
            for f in bool_fields:
                if getattr(item, f, False):
                    symptom_counts[f] = symptom_counts.get(f, 0) + 1

        most_common = sorted(symptom_counts, key=lambda k: symptom_counts[k], reverse=True)[:3]

        insights_md = "**Analyse de vos symptômes de ménopause**\n\nVos données ont été analysées."

        if self.ai_service is not None:
            context = {
                "avg_hot_flash_per_day": avg_hf,
                "most_common_symptoms": most_common,
                "language": user.language,
            }
            try:
                insights_md = await self.ai_service.generate_menopause_insights(context)
            except Exception:
                pass

        return MenopauseInsightsResponse(
            generated_at=datetime.now(timezone.utc),
            insights_markdown=insights_md,
            avg_hot_flash_per_day=avg_hf,
            most_common_symptoms=most_common,
            perimenopause_risk=None,
        )

    # ── Perimenopause screening ───────────────────────────────────────────

    async def perimenopause_screening(
        self, user: User, data: PerimenopauseScreening
    ) -> PerimenopauseScreeningResult:
        signs = []
        if data.irregular_cycles:
            signs.append("cycles irréguliers")
        if data.hot_flashes:
            signs.append("bouffées de chaleur")
        if data.night_sweats:
            signs.append("sueurs nocturnes")
        if data.vaginal_dryness:
            signs.append("sécheresse vaginale")
        if data.sleep_issues:
            signs.append("troubles du sommeil")
        if data.mood_changes:
            signs.append("changements d'humeur")
        if data.brain_fog:
            signs.append("brouillard mental")

        count = len(signs)
        if count >= 4 or (count >= 2 and data.age >= 45):
            risk = "élevé"
        elif count >= 2:
            risk = "modéré"
        else:
            risk = "faible"

        recommendations = [
            "Consultez un gynécologue pour un bilan hormonal (FSH, œstradiol)",
            "Tenez un journal de vos symptômes avec FlorNya",
            "Adoptez une alimentation riche en phyto-estrogènes (soja, graines de lin)",
            "Pratiquez une activité physique régulière pour la santé osseuse",
            "Renseignez-vous sur le THS avec votre médecin si les symptômes sont invalidants",
        ]

        if self.ai_service is not None and count > 0:
            try:
                ai_text = await self.ai_service.perimenopause_assessment(signs, data.age, user.language)
                recommendations.append(ai_text)
            except Exception:
                pass

        return PerimenopauseScreeningResult(
            risk_level=risk,
            detected_signs=signs,
            recommendations=recommendations,
        )

    # ── PDF export ────────────────────────────────────────────────────────

    async def export_pdf(self, user: User) -> bytes:
        from datetime import timedelta
        from jinja2 import Environment, FileSystemLoader
        from pathlib import Path
        import weasyprint
        import datetime as dt

        cutoff = date.today() - timedelta(days=90)
        items = await self.menopause_repo.list_range(
            user_id=user.id, date_from=cutoff, date_to=date.today()
        )
        records = [
            {
                "log_date": str(e.log_date),
                "hot_flash_count": e.hot_flash_count or 0,
                "night_sweats": "Oui" if e.night_sweats else "Non",
                "insomnia": "Oui" if e.insomnia else "Non",
                "mood_swings": "Oui" if e.mood_swings else "Non",
                "severity": e.severity or "–",
                "notes": decrypt_sensitive(e.notes_encrypted) or "",
            }
            for e in items
        ]
        template_dir = Path(__file__).parent.parent / "templates" / "pdf"
        env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)
        tmpl = env.get_template("menopause_report.html")
        html_str = tmpl.render(
            user_name=user.first_name or user.email,
            records=records,
            generated_at=dt.datetime.now(timezone.utc).strftime("%d/%m/%Y"),
        )
        return weasyprint.HTML(string=html_str).write_pdf()

    # ── Private helpers ───────────────────────────────────────────────────

    def _to_public(self, entity: MenopauseLog) -> MenopauseLogPublic:
        return MenopauseLogPublic(
            id=entity.id,
            user_id=entity.user_id,
            log_date=entity.log_date,
            hot_flash_count=entity.hot_flash_count,
            night_sweats=entity.night_sweats,
            vaginal_dryness=entity.vaginal_dryness,
            insomnia=entity.insomnia,
            mood_swings=entity.mood_swings,
            weight_gain=entity.weight_gain,
            brain_fog=entity.brain_fog,
            joint_pain=entity.joint_pain,
            severity=entity.severity,
            notes=decrypt_sensitive(entity.notes_encrypted),
            created_at=entity.created_at,
        )

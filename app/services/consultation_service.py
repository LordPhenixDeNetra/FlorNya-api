import calendar
from datetime import datetime, timezone
from uuid import UUID

from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_sensitive, encrypt_sensitive
from app.models.consultation_booking import ConsultationBooking, ConsultationStatus
from app.models.user import User
from app.repositories.consultation_repository import ConsultationRepository
from app.schemas.consultation import (
    ConsultationBookingCreate,
    ConsultationBookingPublic,
    ConsultationPrepResponse,
)
from app.services.ai.anthropic_service import AnthropicInsightService


class ConsultationService:
    def __init__(
        self,
        session: AsyncSession,
        consultation_repo: ConsultationRepository,
        ai_service: AnthropicInsightService | None = None,
    ):
        self.session = session
        self.consultation_repo = consultation_repo
        self.ai_service = ai_service

    async def book_consultation(self, user: User, data: ConsultationBookingCreate) -> ConsultationBookingPublic:
        booking = await self.consultation_repo.create(
            user_id=user.id,
            scheduled_at=data.scheduled_at,
            practitioner_name=data.practitioner_name,
        )
        await self.session.commit()
        await self.session.refresh(booking)
        return self._to_public(booking)

    async def list_consultations(self, user: User) -> list[ConsultationBookingPublic]:
        bookings = await self.consultation_repo.list_by_user(user.id)
        return [self._to_public(b) for b in bookings]

    async def get_consultation_prep(self, user: User) -> ConsultationPrepResponse:
        from datetime import date, timedelta
        from app.models.cycle_record import CycleRecord
        from app.models.symptom_log import SymptomLog
        from app.models.mood_log import MoodLog
        from app.models.hormonal_treatment import HormonalTreatment

        cutoff = date.today() - timedelta(days=30)

        cycle_result = await self.session.execute(
            select(CycleRecord).where(CycleRecord.user_id == user.id).order_by(CycleRecord.period_start.desc()).limit(3)
        )
        cycles = list(cycle_result.scalars().all())
        cycle_summary = f"{len(cycles)} cycle(s) enregistré(s) ces 30 derniers jours"
        if cycles:
            avg_len = sum(c.cycle_length or 28 for c in cycles) / len(cycles)
            cycle_summary = f"Cycle moyen : {avg_len:.0f} jours, dernières règles : {cycles[0].period_start}"

        sym_result = await self.session.execute(
            select(SymptomLog).where(SymptomLog.user_id == user.id, SymptomLog.log_date >= cutoff)
        )
        symptoms_list = list(sym_result.scalars().all())
        recent_symptoms = []
        if any(s.cramps for s in symptoms_list):
            recent_symptoms.append("Crampes")
        if any(s.fatigue for s in symptoms_list):
            recent_symptoms.append("Fatigue")
        if any(s.headache for s in symptoms_list):
            recent_symptoms.append("Maux de tête")
        if any(s.bloating for s in symptoms_list):
            recent_symptoms.append("Ballonnements")

        mood_result = await self.session.execute(
            select(MoodLog.mood_score).where(MoodLog.user_id == user.id, MoodLog.log_date >= cutoff)
        )
        mood_scores = list(mood_result.scalars().all())
        avg_mood = f"{sum(mood_scores)/len(mood_scores):.1f}/5" if mood_scores else "non renseigné"

        tx_result = await self.session.execute(
            select(HormonalTreatment).where(HormonalTreatment.user_id == user.id, HormonalTreatment.is_active == True)  # noqa: E712
        )
        treatments = [t.treatment_type.value for t in tx_result.scalars().all()]

        context = {
            "language": user.language,
            "cycle_summary": cycle_summary,
            "recent_symptoms": recent_symptoms,
            "avg_mood": avg_mood,
            "treatments": treatments,
            "concerns": [],
        }

        full_notes = "Préparation de consultation non disponible."
        if self.ai_service:
            full_notes = await self.ai_service.generate_consultation_prep(context)

        suggested_questions = [
            "Mes cycles sont-ils normaux ?",
            "Quels examens me recommandez-vous ?",
            "Y a-t-il des signaux d'alarme dans mes symptômes ?",
            "Ma contraception actuelle est-elle adaptée ?",
        ]

        return ConsultationPrepResponse(
            generated_at=datetime.now(timezone.utc),
            cycle_summary=cycle_summary,
            recent_symptoms=recent_symptoms,
            mood_summary=f"Humeur moyenne : {avg_mood}",
            suggested_questions=suggested_questions,
            key_concerns=recent_symptoms[:3],
            full_prep_notes=full_notes,
        )

    async def generate_monthly_pdf(self, user: User, year: int, month: int) -> bytes:
        from datetime import date
        from jinja2 import Environment, FileSystemLoader
        import weasyprint
        import os
        from app.models.cycle_record import CycleRecord
        from app.models.symptom_log import SymptomLog
        from app.models.mood_log import MoodLog
        from app.models.nutrition_log import NutritionLog

        month_start = date(year, month, 1)
        month_end = date(year, month, calendar.monthrange(year, month)[1])

        cycle_result = await self.session.execute(
            select(CycleRecord).where(
                CycleRecord.user_id == user.id,
                CycleRecord.period_start >= month_start,
                CycleRecord.period_start <= month_end,
            )
        )
        cycles = list(cycle_result.scalars().all())

        mood_result = await self.session.execute(
            select(MoodLog).where(
                MoodLog.user_id == user.id,
                MoodLog.log_date >= month_start,
                MoodLog.log_date <= month_end,
            ).order_by(MoodLog.log_date)
        )
        moods = list(mood_result.scalars().all())

        sym_result = await self.session.execute(
            select(SymptomLog).where(
                SymptomLog.user_id == user.id,
                SymptomLog.log_date >= month_start,
                SymptomLog.log_date <= month_end,
            ).order_by(SymptomLog.log_date)
        )
        symptoms = list(sym_result.scalars().all())

        nutri_result = await self.session.execute(
            select(NutritionLog).where(
                NutritionLog.user_id == user.id,
                NutritionLog.log_date >= month_start,
                NutritionLog.log_date <= month_end,
            )
        )
        nutrition_logs = list(nutri_result.scalars().all())

        avg_mood = f"{sum(m.mood_score for m in moods)/len(moods):.1f}/5" if moods else "N/A"
        avg_nutri = f"{sum(n.hormonal_impact_score or 5 for n in nutrition_logs)/len(nutrition_logs):.1f}/10" if nutrition_logs else "N/A"

        monthly_summary = ""
        if self.ai_service:
            month_names_fr = ["", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
            monthly_summary = await self.ai_service.generate_monthly_report_insights({
                "language": user.language,
                "month_name": month_names_fr[month],
                "cycle_count": len(cycles),
                "avg_mood": avg_mood,
                "top_symptoms": ["crampes", "fatigue"] if symptoms else [],
                "avg_nutrition_score": avg_nutri,
            })

        mood_records = [{"log_date": str(m.log_date), "mood_score": m.mood_score} for m in moods]
        symptom_records = [{
            "log_date": str(s.log_date),
            "cramps": "Oui" if s.cramps else "Non",
            "fatigue": "Oui" if s.fatigue else "Non",
            "bloating": "Oui" if s.bloating else "Non",
            "energy": s.energy or "–",
        } for s in symptoms]
        cycle_records = [{
            "period_start": str(c.period_start),
            "cycle_length": c.cycle_length or "–",
            "flow_intensity": c.flow_intensity.value if c.flow_intensity else "–",
        } for c in cycles]

        templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates", "pdf")
        env = Environment(loader=FileSystemLoader(templates_dir), autoescape=True)
        template = env.get_template("monthly_report.html")

        html = template.render(
            user_name=user.first_name or user.email.split("@")[0],
            generated_at=datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M"),
            month_label=f"{['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'][month]} {year}",
            cycle_records=cycle_records,
            mood_records=mood_records,
            symptom_records=symptom_records,
            avg_mood=avg_mood,
            avg_nutrition_score=avg_nutri,
            monthly_summary=monthly_summary,
        )
        return weasyprint.HTML(string=html).write_pdf()

    def _to_public(self, booking: ConsultationBooking) -> ConsultationBookingPublic:
        return ConsultationBookingPublic(
            id=booking.id,
            user_id=booking.user_id,
            scheduled_at=booking.scheduled_at,
            status=booking.status.value,
            practitioner_name=booking.practitioner_name,
            preparation_notes=decrypt_sensitive(booking.preparation_notes_encrypted),
            video_url=decrypt_sensitive(booking.video_url_encrypted),
            summary=decrypt_sensitive(booking.summary_encrypted),
            created_at=booking.created_at,
        )

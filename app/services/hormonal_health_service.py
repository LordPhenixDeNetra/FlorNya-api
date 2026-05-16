import json
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_sensitive, encrypt_sensitive
from app.models.hormonal_treatment import HormonalTreatment, TreatmentType
from app.models.pain_log import PainLog
from app.models.user import User
from app.repositories.hormonal_health_repository import HormonalTreatmentRepository, PainLogRepository
from app.schemas.hormonal_health import (
    EndoResourcesResponse,
    HormonalTreatmentCreate,
    HormonalTreatmentPublic,
    PCOSRiskAssessment,
    PCOSRiskResponse,
    PainLogCreate,
    PainLogPublic,
    TreatmentType as TreatmentTypeSchema,
)


_PCOS_RECOMMENDATIONS = {
    "low": ["Suivi médical de routine", "Alimentation équilibrée riche en fibres"],
    "medium": [
        "Consultez un gynécologue pour bilan hormonal",
        "Adoptez une alimentation anti-inflammatoire (index glycémique bas)",
        "30 min d'activité physique modérée par jour",
        "Réduire le stress (yoga, méditation)",
        "Suppléments : inositol, vitamine D, magnésium",
    ],
    "high": [
        "Consultez rapidement un gynécologue endocrinologue",
        "Demandez un bilan hormonal complet (testostérone, LH, FSH, insuline)",
        "Régime alimentaire à IG bas strict",
        "Évaluation traitement : contraceptif hormonal ou metformine",
        "Surveillance des complications cardiovasculaires",
    ],
}


class HormonalHealthService:
    def __init__(
        self,
        session: AsyncSession,
        pain_repo: PainLogRepository,
        treatment_repo: HormonalTreatmentRepository,
        ai_service: object | None = None,
    ):
        self.session = session
        self.pain_repo = pain_repo
        self.treatment_repo = treatment_repo
        self.ai_service = ai_service

    # ── Pain journal ──────────────────────────────────────────────────────

    async def log_pain(self, user: User, data: PainLogCreate) -> PainLogPublic:
        body_zones_str = json.dumps(data.body_zones) if data.body_zones else None
        entity = await self.pain_repo.upsert(
            user_id=user.id,
            log_date=data.log_date,
            pain_intensity=data.pain_intensity,
            pelvic=data.pelvic,
            lower_back=data.lower_back,
            dysmenorrhea=data.dysmenorrhea,
            dyspareunia=data.dyspareunia,
            bloating=data.bloating,
            body_zones=body_zones_str,
            notes_encrypted=encrypt_sensitive(data.notes),
        )
        await self.session.commit()
        await self.session.refresh(entity)
        return self._pain_to_public(entity)

    async def list_pain_logs(
        self, user: User, date_from: date | None = None, date_to: date | None = None
    ) -> list[PainLogPublic]:
        items = await self.pain_repo.list_range(
            user_id=user.id, date_from=date_from, date_to=date_to
        )
        return [self._pain_to_public(e) for e in items]

    async def export_pain_pdf(self, user: User) -> bytes:
        from datetime import timedelta
        from jinja2 import Environment, FileSystemLoader
        from pathlib import Path
        import weasyprint

        cutoff = date.today() - timedelta(days=90)
        items = await self.pain_repo.list_range(
            user_id=user.id, date_from=cutoff, date_to=date.today()
        )
        records = [
            {
                "log_date": str(e.log_date),
                "pain_intensity": e.pain_intensity or "–",
                "pelvic": "Oui" if e.pelvic else "Non",
                "lower_back": "Oui" if e.lower_back else "Non",
                "dysmenorrhea": "Oui" if e.dysmenorrhea else "Non",
                "dyspareunia": "Oui" if e.dyspareunia else "Non",
                "notes": decrypt_sensitive(e.notes_encrypted) or "",
            }
            for e in items
        ]
        template_dir = Path(__file__).parent.parent / "templates" / "pdf"
        env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)
        tmpl = env.get_template("pain_report.html")
        html_str = tmpl.render(
            user_name=user.first_name or user.email,
            records=records,
            generated_at=__import__("datetime").datetime.now().strftime("%d/%m/%Y"),
        )
        return weasyprint.HTML(string=html_str).write_pdf()

    # ── PCOS risk ─────────────────────────────────────────────────────────

    async def pcos_risk_assessment(
        self, user: User, data: PCOSRiskAssessment
    ) -> PCOSRiskResponse:
        fields = [
            data.irregular_cycles, data.excess_hair_growth, data.acne,
            data.weight_gain, data.hair_loss, data.difficulty_conceiving,
            data.mood_swings, data.fatigue,
        ]
        score = sum(1 for f in fields if f)
        max_score = len(fields)

        if score >= 5:
            risk = "high"
        elif score >= 3:
            risk = "medium"
        else:
            risk = "low"

        recommendations = _PCOS_RECOMMENDATIONS[risk].copy()

        if self.ai_service is not None and risk != "low":
            symptom_names = []
            mapping = {
                "irregular_cycles": "cycles irréguliers",
                "excess_hair_growth": "pilosité excessive",
                "acne": "acné hormonale",
                "weight_gain": "prise de poids",
                "hair_loss": "chute de cheveux",
                "difficulty_conceiving": "difficultés à concevoir",
                "mood_swings": "sautes d'humeur",
                "fatigue": "fatigue",
            }
            for field_name, label in mapping.items():
                if getattr(data, field_name, False):
                    symptom_names.append(label)
            try:
                ai_advice = await self.ai_service.pcos_advice(symptom_names, user.language)
                recommendations.append(f"\n{ai_advice}")
            except Exception:
                pass

        return PCOSRiskResponse(
            risk_level=risk,
            score=score,
            max_score=max_score,
            recommendations=recommendations,
        )

    # ── Endometriosis resources ───────────────────────────────────────────

    def get_endo_resources(self) -> EndoResourcesResponse:
        return EndoResourcesResponse(
            description=(
                "L'endométriose est une maladie chronique où du tissu similaire à l'endomètre "
                "se développe en dehors de l'utérus. Elle touche 10% des femmes en âge de procréer."
            ),
            common_symptoms=[
                "Douleurs pelviennes intenses, surtout pendant les règles",
                "Douleurs pendant les rapports (dyspareunie)",
                "Règles abondantes ou irrégulières",
                "Douleurs lors des selles ou urines",
                "Difficultés à concevoir",
                "Fatigue chronique",
            ],
            diagnostic_tests=[
                "Examen clinique gynécologique",
                "Échographie pelvienne (transvaginale)",
                "IRM pelvienne",
                "Cœlioscopie (seul examen de certitude)",
                "Bilan CA-125 (non spécifique)",
            ],
            questions_for_doctor=[
                "Quels examens me recommandez-vous en premier ?",
                "Y a-t-il un traitement hormonal adapté à mon cas ?",
                "Quel impact sur ma fertilité ?",
                "Centres spécialisés endométriose (ENDOMEDICAL, ENDOFRANCE) ?",
                "Comment gérer la douleur au quotidien ?",
            ],
            disclaimer=(
                "Ces informations sont indicatives. Consultez un gynécologue spécialisé "
                "pour un diagnostic et un traitement adaptés."
            ),
        )

    # ── Hormonal treatments ───────────────────────────────────────────────

    async def add_treatment(self, user: User, data: HormonalTreatmentCreate) -> HormonalTreatmentPublic:
        if data.end_date is None:
            await self.treatment_repo.deactivate_all(user.id)

        treatment_type = TreatmentType(data.treatment_type.value)
        entity = HormonalTreatment(
            user_id=user.id,
            treatment_type=treatment_type,
            brand_name=data.brand_name,
            start_date=data.start_date,
            end_date=data.end_date,
            is_active=(data.end_date is None),
            reminder_time=data.reminder_time,
            side_effects_encrypted=encrypt_sensitive(data.side_effects),
            notes_encrypted=encrypt_sensitive(data.notes),
        )
        await self.treatment_repo.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return self._treatment_to_public(entity)

    async def list_treatments(self, user: User, active_only: bool = False) -> list[HormonalTreatmentPublic]:
        items = await self.treatment_repo.list_by_user(user.id, active_only=active_only)
        return [self._treatment_to_public(e) for e in items]

    # ── Private helpers ───────────────────────────────────────────────────

    def _pain_to_public(self, entity: PainLog) -> PainLogPublic:
        zones = None
        if entity.body_zones:
            try:
                zones = json.loads(entity.body_zones)
            except (json.JSONDecodeError, TypeError):
                zones = [entity.body_zones]
        return PainLogPublic(
            id=entity.id,
            user_id=entity.user_id,
            log_date=entity.log_date,
            pain_intensity=entity.pain_intensity,
            pelvic=entity.pelvic,
            lower_back=entity.lower_back,
            dysmenorrhea=entity.dysmenorrhea,
            dyspareunia=entity.dyspareunia,
            bloating=entity.bloating,
            body_zones=zones,
            notes=decrypt_sensitive(entity.notes_encrypted),
            created_at=entity.created_at,
        )

    def _treatment_to_public(self, entity: HormonalTreatment) -> HormonalTreatmentPublic:
        return HormonalTreatmentPublic(
            id=entity.id,
            user_id=entity.user_id,
            treatment_type=TreatmentTypeSchema(entity.treatment_type.value),
            brand_name=entity.brand_name,
            start_date=entity.start_date,
            end_date=entity.end_date,
            is_active=entity.is_active,
            reminder_time=entity.reminder_time,
            side_effects=decrypt_sensitive(entity.side_effects_encrypted),
            notes=decrypt_sensitive(entity.notes_encrypted),
            created_at=entity.created_at,
        )

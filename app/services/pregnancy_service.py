import json
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_sensitive, encrypt_sensitive
from app.models.breastfeeding_session import BreastSide, BreastfeedingSession
from app.models.epds_assessment import EPDS_ALERT_THRESHOLD, EPDS_MODERATE_THRESHOLD, EPDSAssessment
from app.models.pregnancy_appointment import AppointmentType, PregnancyAppointment
from app.models.pregnancy_profile import PregnancyProfile, PregnancyStatus
from app.models.pregnancy_symptom_log import PregnancySymptomLog
from app.models.user import User
from app.repositories.pregnancy_repository import (
    AppointmentRepository,
    BreastfeedingRepository,
    EPDSRepository,
    PregnancyProfileRepository,
    PregnancySymptomRepository,
)
from app.schemas.pregnancy import (
    AppointmentCreate,
    AppointmentPublic,
    AppointmentType as AppTypeSchema,
    BreastSide as BreastSideSchema,
    BreastfeedingSessionCreate,
    BreastfeedingSessionPublic,
    EPDSCreate,
    EPDSPublic,
    PostpartumActivate,
    PregnancyActivate,
    PregnancyProfilePublic,
    PregnancyStatus as StatusSchema,
    PregnancySymptomCreate,
    PregnancySymptomPublic,
    PregnancyWeekInfo,
)

_WEEK_DATA: dict[int, dict] = {
    4: {"size": "un grain de riz", "length_cm": 0.4, "weight_g": None, "development": "Le cœur commence à battre.", "tips": "Commencez l'acide folique si ce n'est pas déjà fait."},
    8: {"size": "une fraise", "length_cm": 1.6, "weight_g": 1, "development": "Les doigts se forment. Le cœur bat à 150 bpm.", "tips": "Évitez la caféine et l'alcool."},
    12: {"size": "une prune", "length_cm": 5.4, "weight_g": 14, "development": "Les organes sont formés. Le risque de fausse-couche diminue.", "tips": "1er trimestre bientôt terminé — dites-le à vos proches !"},
    16: {"size": "un avocat", "length_cm": 11.6, "weight_g": 100, "development": "Mouvements actifs. Le sexe peut être visible.", "tips": "Dormez sur le côté gauche pour améliorer la circulation."},
    20: {"size": "une banane", "length_cm": 25.6, "weight_g": 300, "development": "Vous pouvez sentir les mouvements.", "tips": "Morphologie à faire. Continuez le sport adapté."},
    24: {"size": "un épi de maïs", "length_cm": 30.0, "weight_g": 600, "development": "Les poumons se développent. Visage expressif.", "tips": "Test de glucose à prévoir bientôt."},
    28: {"size": "une aubergine", "length_cm": 37.6, "weight_g": 1005, "development": "Ouvre les yeux. Capte la voix de la mère.", "tips": "3e trimestre ! Préparez votre valise de maternité."},
    32: {"size": "un chou-fleur", "length_cm": 42.4, "weight_g": 1702, "development": "Stocke les graisses. Position tête en bas.", "tips": "Cours de préparation à l'accouchement."},
    36: {"size": "un melon", "length_cm": 47.4, "weight_g": 2622, "development": "Presque à terme. Poumons presque matures.", "tips": "Congé maternité — profitez du repos."},
    40: {"size": "une pastèque", "length_cm": 51.2, "weight_g": 3400, "development": "À terme ! Prêt pour la naissance.", "tips": "Sac prêt ? Signes du travail : contractions régulières, perte des eaux."},
}


def _get_week_info(week: int) -> dict:
    best_key = max((k for k in _WEEK_DATA if k <= week), default=4)
    return _WEEK_DATA[best_key]


_ALARM_SYMPTOMS = {
    "headache": True,
    "swelling": True,
}


class PregnancyService:
    def __init__(
        self,
        session: AsyncSession,
        pregnancy_profiles: PregnancyProfileRepository,
        pregnancy_symptoms: PregnancySymptomRepository,
        appointments: AppointmentRepository,
        breastfeeding: BreastfeedingRepository,
        epds: EPDSRepository,
        ai_service: object | None = None,
    ):
        self.session = session
        self.pregnancy_profiles = pregnancy_profiles
        self.pregnancy_symptoms = pregnancy_symptoms
        self.appointments = appointments
        self.breastfeeding = breastfeeding
        self.epds = epds
        self.ai_service = ai_service

    # ── Pregnancy mode ────────────────────────────────────────────────────

    async def activate_pregnancy(self, user: User, data: PregnancyActivate) -> PregnancyProfilePublic:
        existing = await self.pregnancy_profiles.get_by_user(user.id)
        if existing is not None:
            existing.status = PregnancyStatus.active
            existing.lmp_date = data.lmp_date
            existing.due_date = data.due_date
            existing.weeks_at_activation = data.weeks_at_activation
            await self.session.flush()
            entity = existing
        else:
            entity = PregnancyProfile(
                user_id=user.id,
                status=PregnancyStatus.active,
                lmp_date=data.lmp_date,
                due_date=data.due_date,
                weeks_at_activation=data.weeks_at_activation,
            )
            await self.pregnancy_profiles.add(entity)

        from app.models.female_profile import ReproductiveStage
        from app.models.female_profile import FemaleProfile
        from sqlalchemy import select
        result = await self.session.execute(
            select(FemaleProfile).where(FemaleProfile.user_id == user.id)
        )
        profile = result.scalar_one_or_none()
        if profile:
            profile.reproductive_stage = ReproductiveStage.pregnant

        await self.session.commit()
        await self.session.refresh(entity)
        return self._profile_to_public(entity)

    async def get_pregnancy_profile(self, user: User) -> PregnancyProfilePublic | None:
        entity = await self.pregnancy_profiles.get_by_user(user.id)
        if entity is None:
            return None
        return self._profile_to_public(entity)

    async def activate_postpartum(self, user: User, data: PostpartumActivate) -> PregnancyProfilePublic:
        existing = await self.pregnancy_profiles.get_by_user(user.id)
        if existing is not None:
            existing.status = PregnancyStatus.postpartum
            existing.delivery_date = data.delivery_date
            await self.session.flush()
            entity = existing
        else:
            entity = PregnancyProfile(
                user_id=user.id,
                status=PregnancyStatus.postpartum,
                delivery_date=data.delivery_date,
            )
            await self.pregnancy_profiles.add(entity)

        from app.models.female_profile import ReproductiveStage, FemaleProfile
        from sqlalchemy import select
        result = await self.session.execute(
            select(FemaleProfile).where(FemaleProfile.user_id == user.id)
        )
        profile = result.scalar_one_or_none()
        if profile:
            profile.reproductive_stage = ReproductiveStage.postpartum

        await self.session.commit()
        await self.session.refresh(entity)
        return self._profile_to_public(entity)

    # ── Week info ─────────────────────────────────────────────────────────

    def get_week_info(self, week: int) -> PregnancyWeekInfo:
        week = max(1, min(42, week))
        trimester = 1 if week <= 13 else (2 if week <= 26 else 3)
        data = _get_week_info(week)
        return PregnancyWeekInfo(
            week=week,
            trimester=trimester,
            baby_size_comparison=data["size"],
            baby_length_cm=data["length_cm"],
            baby_weight_g=data["weight_g"],
            key_development=data["development"],
            tips_for_mother=data["tips"],
        )

    # ── Pregnancy symptoms ────────────────────────────────────────────────

    async def log_pregnancy_symptom(
        self, user: User, data: PregnancySymptomCreate, current_week: int | None
    ) -> PregnancySymptomPublic:
        is_alarm = (
            (data.swelling or False) and (data.headache or False) and
            (data.severity or 0) >= 4
        )

        entity = await self.pregnancy_symptoms.upsert(
            user_id=user.id,
            log_date=data.log_date,
            nausea=data.nausea,
            vomiting=data.vomiting,
            fatigue=data.fatigue,
            back_pain=data.back_pain,
            swelling=data.swelling,
            heartburn=data.heartburn,
            headache=data.headache,
            fetal_movement_count=data.fetal_movement_count,
            severity=data.severity,
            is_alarm_symptom=is_alarm,
            notes_encrypted=encrypt_sensitive(data.notes),
        )
        await self.session.commit()
        await self.session.refresh(entity)
        return self._symptom_to_public(entity)

    async def list_pregnancy_symptoms(
        self, user: User, date_from: date | None = None, date_to: date | None = None
    ) -> list[PregnancySymptomPublic]:
        items = await self.pregnancy_symptoms.list_range(
            user_id=user.id, date_from=date_from, date_to=date_to
        )
        return [self._symptom_to_public(e) for e in items]

    # ── Appointments ──────────────────────────────────────────────────────

    async def create_appointment(self, user: User, data: AppointmentCreate) -> AppointmentPublic:
        app_type = AppointmentType(data.appointment_type.value)
        entity = PregnancyAppointment(
            user_id=user.id,
            appointment_date=data.appointment_date,
            appointment_type=app_type,
            title=data.title,
            location=data.location,
            notes_encrypted=encrypt_sensitive(data.notes),
        )
        await self.appointments.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return self._appointment_to_public(entity)

    async def list_appointments(self, user: User, upcoming_only: bool = False) -> list[AppointmentPublic]:
        if upcoming_only:
            items = await self.appointments.list_upcoming(user.id, date.today())
        else:
            items = await self.appointments.list_by_user(user.id)
        return [self._appointment_to_public(e) for e in items]

    # ── Breastfeeding ─────────────────────────────────────────────────────

    async def log_breastfeeding(
        self, user: User, data: BreastfeedingSessionCreate
    ) -> BreastfeedingSessionPublic:
        side = BreastSide(data.breast_side.value) if data.breast_side else None
        entity = BreastfeedingSession(
            user_id=user.id,
            session_date=data.session_date,
            started_at=data.started_at,
            duration_minutes=data.duration_minutes,
            breast_side=side,
            quantity_ml=data.quantity_ml,
        )
        await self.breastfeeding.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return self._breastfeeding_to_public(entity)

    async def list_breastfeeding(
        self, user: User, date_from: date | None = None, date_to: date | None = None
    ) -> list[BreastfeedingSessionPublic]:
        items = await self.breastfeeding.list_range(
            user_id=user.id, date_from=date_from, date_to=date_to
        )
        return [self._breastfeeding_to_public(e) for e in items]

    # ── EPDS ──────────────────────────────────────────────────────────────

    async def submit_epds(self, user: User, data: EPDSCreate) -> EPDSPublic:
        total = sum(data.answers)
        answers_encrypted = encrypt_sensitive(json.dumps(data.answers))

        is_alert = total >= EPDS_ALERT_THRESHOLD
        entity = EPDSAssessment(
            user_id=user.id,
            assessment_date=date.today(),
            total_score=total,
            answers_encrypted=answers_encrypted,
            alert_sent=False,
        )
        await self.epds.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)

        if is_alert and self.ai_service is not None:
            try:
                message = await self.ai_service.generate_postpartum_message(total, user.language)
                entity.alert_sent = True
                await self.session.commit()
            except Exception:
                pass

        return self._epds_to_public(entity)

    # ── Private helpers ───────────────────────────────────────────────────

    def _profile_to_public(self, entity: PregnancyProfile) -> PregnancyProfilePublic:
        current_week: int | None = None
        if entity.lmp_date and entity.status == PregnancyStatus.active:
            days = (date.today() - entity.lmp_date).days
            current_week = min(42, max(1, days // 7))
        elif entity.weeks_at_activation:
            current_week = entity.weeks_at_activation

        return PregnancyProfilePublic(
            id=entity.id,
            user_id=entity.user_id,
            status=StatusSchema(entity.status.value),
            lmp_date=entity.lmp_date,
            due_date=entity.due_date,
            delivery_date=entity.delivery_date,
            is_breastfeeding=entity.is_breastfeeding,
            current_week=current_week,
            created_at=entity.created_at,
        )

    def _symptom_to_public(self, entity: PregnancySymptomLog) -> PregnancySymptomPublic:
        return PregnancySymptomPublic(
            id=entity.id,
            user_id=entity.user_id,
            log_date=entity.log_date,
            nausea=entity.nausea,
            vomiting=entity.vomiting,
            fatigue=entity.fatigue,
            back_pain=entity.back_pain,
            swelling=entity.swelling,
            heartburn=entity.heartburn,
            headache=entity.headache,
            fetal_movement_count=entity.fetal_movement_count,
            severity=entity.severity,
            is_alarm_symptom=entity.is_alarm_symptom,
            notes=decrypt_sensitive(entity.notes_encrypted),
            created_at=entity.created_at,
        )

    def _appointment_to_public(self, entity: PregnancyAppointment) -> AppointmentPublic:
        return AppointmentPublic(
            id=entity.id,
            user_id=entity.user_id,
            appointment_date=entity.appointment_date,
            appointment_type=AppTypeSchema(entity.appointment_type.value),
            title=entity.title,
            location=entity.location,
            notes=decrypt_sensitive(entity.notes_encrypted),
            created_at=entity.created_at,
        )

    def _breastfeeding_to_public(self, entity: BreastfeedingSession) -> BreastfeedingSessionPublic:
        side = BreastSideSchema(entity.breast_side.value) if entity.breast_side else None
        return BreastfeedingSessionPublic(
            id=entity.id,
            user_id=entity.user_id,
            session_date=entity.session_date,
            started_at=entity.started_at,
            duration_minutes=entity.duration_minutes,
            breast_side=side,
            quantity_ml=entity.quantity_ml,
            created_at=entity.created_at,
        )

    def _epds_to_public(self, entity: EPDSAssessment) -> EPDSPublic:
        score = entity.total_score
        if score >= EPDS_ALERT_THRESHOLD:
            alert_level = "alert"
            message = (
                "⚠️ Votre score suggère une dépression post-partum potentielle. "
                "Nous vous encourageons vivement à consulter votre médecin ou appeler le 3114 (numéro national de prévention du suicide)."
            )
        elif score >= EPDS_MODERATE_THRESHOLD:
            alert_level = "moderate"
            message = (
                "Votre score indique quelques difficultés. Prenez soin de vous. "
                "Parlez de vos émotions à un proche ou à votre sage-femme."
            )
        else:
            alert_level = "normal"
            message = "Votre score est rassurant. Continuez à prendre soin de vous et à vous reposer !"

        return EPDSPublic(
            id=entity.id,
            user_id=entity.user_id,
            assessment_date=entity.assessment_date,
            total_score=score,
            alert_level=alert_level,
            message=message,
            created_at=entity.created_at,
        )

from uuid import UUID

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.database import get_async_session
from app.core.security import decode_token, is_adult
from app.models.user import User, UserPlan
from app.repositories.challenge_repository import ChallengeRepository, UserChallengeRepository
from app.repositories.device_token_repository import DeviceTokenRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.community_repository import CommunityPostRepository, CommunityRecipeRepository
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.cycle_repository import CycleRepository
from app.repositories.emotional_journal_repository import EmotionalJournalRepository
from app.repositories.female_profile_repository import FemaleProfileRepository
from app.repositories.fertility_repository import ConceptionAttemptRepository, FertilityRepository
from app.repositories.hormonal_health_repository import HormonalTreatmentRepository, PainLogRepository
from app.repositories.intimate_repository import IntimateHealthRepository, LibidoRepository
from app.repositories.menopause_repository import MenopauseRepository
from app.repositories.mental_alert_repository import MentalAlertRepository
from app.repositories.mood_repository import MoodRepository
from app.repositories.nutrition_repository import NutritionRepository
from app.repositories.pregnancy_repository import (
    AppointmentRepository,
    BreastfeedingRepository,
    EPDSRepository,
    PregnancyProfileRepository,
    PregnancySymptomRepository,
)
from app.repositories.reminder_repository import ReminderRepository
from app.repositories.stripe_invoice_repository import StripeInvoiceRepository
from app.repositories.symptom_repository import SymptomRepository
from app.repositories.user_repository import UserRepository
from app.services.ai.anthropic_service import AnthropicInsightService
from app.services.push_notification_service import PushNotificationService
from app.services.auth_service import AuthService
from app.services.chat_service import ChatService
from app.services.community_service import CommunityService
from app.services.consultation_service import ConsultationService
from app.services.cycle_service import CycleService
from app.services.dashboard_service import DashboardService
from app.services.email_service import EmailService
from app.services.fertility_service import FertilityService
from app.services.hormonal_health_service import HormonalHealthService
from app.services.intimate_service import IntimateService
from app.services.mental_service import MentalService
from app.services.menopause_service import MenopauseService
from app.services.nutrition_service import NutritionService
from app.services.payment_service import PaymentService
from app.services.phase_calculator import PhaseCalculator
from app.services.pregnancy_service import PregnancyService
from app.services.reminder_service import ReminderService
from app.services.user_service import UserService

settings = get_settings()

bearer = HTTPBearer(auto_error=False)

# ── Repository providers ─────────────────────────────────────────────────────


async def get_user_repository(session: AsyncSession = Depends(get_async_session)) -> UserRepository:
    return UserRepository(session)


async def get_female_profile_repository(
    session: AsyncSession = Depends(get_async_session),
) -> FemaleProfileRepository:
    return FemaleProfileRepository(session)


async def get_cycle_repository(session: AsyncSession = Depends(get_async_session)) -> CycleRepository:
    return CycleRepository(session)


async def get_mood_repository(session: AsyncSession = Depends(get_async_session)) -> MoodRepository:
    return MoodRepository(session)


async def get_symptom_repository(
    session: AsyncSession = Depends(get_async_session),
) -> SymptomRepository:
    return SymptomRepository(session)


async def get_reminder_repository(
    session: AsyncSession = Depends(get_async_session),
) -> ReminderRepository:
    return ReminderRepository(session)


async def get_stripe_invoice_repository(
    session: AsyncSession = Depends(get_async_session),
) -> StripeInvoiceRepository:
    return StripeInvoiceRepository(session)


async def get_fertility_repository(
    session: AsyncSession = Depends(get_async_session),
) -> FertilityRepository:
    return FertilityRepository(session)


async def get_conception_attempt_repository(
    session: AsyncSession = Depends(get_async_session),
) -> ConceptionAttemptRepository:
    return ConceptionAttemptRepository(session)


async def get_pregnancy_profile_repository(
    session: AsyncSession = Depends(get_async_session),
) -> PregnancyProfileRepository:
    return PregnancyProfileRepository(session)


async def get_pregnancy_symptom_repository(
    session: AsyncSession = Depends(get_async_session),
) -> PregnancySymptomRepository:
    return PregnancySymptomRepository(session)


async def get_appointment_repository(
    session: AsyncSession = Depends(get_async_session),
) -> AppointmentRepository:
    return AppointmentRepository(session)


async def get_breastfeeding_repository(
    session: AsyncSession = Depends(get_async_session),
) -> BreastfeedingRepository:
    return BreastfeedingRepository(session)


async def get_epds_repository(
    session: AsyncSession = Depends(get_async_session),
) -> EPDSRepository:
    return EPDSRepository(session)


async def get_pain_log_repository(
    session: AsyncSession = Depends(get_async_session),
) -> PainLogRepository:
    return PainLogRepository(session)


async def get_hormonal_treatment_repository(
    session: AsyncSession = Depends(get_async_session),
) -> HormonalTreatmentRepository:
    return HormonalTreatmentRepository(session)


async def get_menopause_repository(
    session: AsyncSession = Depends(get_async_session),
) -> MenopauseRepository:
    return MenopauseRepository(session)


async def get_nutrition_repository(
    session: AsyncSession = Depends(get_async_session),
) -> NutritionRepository:
    return NutritionRepository(session)


# ── Service providers ────────────────────────────────────────────────────────


def get_email_service() -> EmailService:
    return EmailService()


def get_anthropic_service() -> AnthropicInsightService | None:
    if not settings.ANTHROPIC_API_KEY:
        return None
    return AnthropicInsightService()


async def get_auth_service(
    session: AsyncSession = Depends(get_async_session),
    users: UserRepository = Depends(get_user_repository),
    email_service: EmailService = Depends(get_email_service),
) -> AuthService:
    return AuthService(session=session, users=users, email_service=email_service)


async def get_user_service(
    session: AsyncSession = Depends(get_async_session),
    users: UserRepository = Depends(get_user_repository),
    profiles: FemaleProfileRepository = Depends(get_female_profile_repository),
    cycles: CycleRepository = Depends(get_cycle_repository),
    moods: MoodRepository = Depends(get_mood_repository),
) -> UserService:
    return UserService(session=session, users=users, profiles=profiles, cycles=cycles, moods=moods)


async def get_phase_calculator() -> PhaseCalculator:
    return PhaseCalculator()


async def get_cycle_service(
    session: AsyncSession = Depends(get_async_session),
    cycles: CycleRepository = Depends(get_cycle_repository),
    calculator: PhaseCalculator = Depends(get_phase_calculator),
    symptoms: SymptomRepository = Depends(get_symptom_repository),
    moods: MoodRepository = Depends(get_mood_repository),
    ai_service: AnthropicInsightService | None = Depends(get_anthropic_service),
) -> CycleService:
    return CycleService(
        session=session,
        cycles=cycles,
        calculator=calculator,
        symptoms=symptoms,
        moods=moods,
        ai_service=ai_service,
    )


async def get_payment_service(
    session: AsyncSession = Depends(get_async_session),
    users: UserRepository = Depends(get_user_repository),
    invoices: StripeInvoiceRepository = Depends(get_stripe_invoice_repository),
) -> PaymentService:
    return PaymentService(session=session, users=users, invoices=invoices)


async def get_reminder_service(
    session: AsyncSession = Depends(get_async_session),
    reminders: ReminderRepository = Depends(get_reminder_repository),
) -> ReminderService:
    return ReminderService(session=session, reminders=reminders)


async def get_fertility_service(
    session: AsyncSession = Depends(get_async_session),
    fertility_repo: FertilityRepository = Depends(get_fertility_repository),
    conception_repo: ConceptionAttemptRepository = Depends(get_conception_attempt_repository),
    calculator: PhaseCalculator = Depends(get_phase_calculator),
    ai_service: AnthropicInsightService | None = Depends(get_anthropic_service),
) -> FertilityService:
    return FertilityService(
        session=session,
        fertility_repo=fertility_repo,
        conception_repo=conception_repo,
        calculator=calculator,
        ai_service=ai_service,
    )


async def get_pregnancy_service(
    session: AsyncSession = Depends(get_async_session),
    pregnancy_profiles: PregnancyProfileRepository = Depends(get_pregnancy_profile_repository),
    pregnancy_symptoms: PregnancySymptomRepository = Depends(get_pregnancy_symptom_repository),
    appointments: AppointmentRepository = Depends(get_appointment_repository),
    breastfeeding: BreastfeedingRepository = Depends(get_breastfeeding_repository),
    epds: EPDSRepository = Depends(get_epds_repository),
    ai_service: AnthropicInsightService | None = Depends(get_anthropic_service),
) -> PregnancyService:
    return PregnancyService(
        session=session,
        pregnancy_profiles=pregnancy_profiles,
        pregnancy_symptoms=pregnancy_symptoms,
        appointments=appointments,
        breastfeeding=breastfeeding,
        epds=epds,
        ai_service=ai_service,
    )


async def get_hormonal_health_service(
    session: AsyncSession = Depends(get_async_session),
    pain_repo: PainLogRepository = Depends(get_pain_log_repository),
    treatment_repo: HormonalTreatmentRepository = Depends(get_hormonal_treatment_repository),
    ai_service: AnthropicInsightService | None = Depends(get_anthropic_service),
) -> HormonalHealthService:
    return HormonalHealthService(
        session=session,
        pain_repo=pain_repo,
        treatment_repo=treatment_repo,
        ai_service=ai_service,
    )


async def get_menopause_service(
    session: AsyncSession = Depends(get_async_session),
    menopause_repo: MenopauseRepository = Depends(get_menopause_repository),
    ai_service: AnthropicInsightService | None = Depends(get_anthropic_service),
) -> MenopauseService:
    return MenopauseService(
        session=session,
        menopause_repo=menopause_repo,
        ai_service=ai_service,
    )


async def get_nutrition_service(
    session: AsyncSession = Depends(get_async_session),
    nutrition_repo: NutritionRepository = Depends(get_nutrition_repository),
    ai_service: AnthropicInsightService | None = Depends(get_anthropic_service),
) -> NutritionService:
    return NutritionService(
        session=session,
        nutrition_repo=nutrition_repo,
        ai_service=ai_service,
    )


# ── Extras — Repository providers ───────────────────────────────────────────


async def get_device_token_repository(
    session: AsyncSession = Depends(get_async_session),
) -> DeviceTokenRepository:
    return DeviceTokenRepository(session)


def get_push_notification_service() -> PushNotificationService:
    return PushNotificationService()


# ── Phase 3 — Repository providers ──────────────────────────────────────────


async def get_emotional_journal_repository(
    session: AsyncSession = Depends(get_async_session),
) -> EmotionalJournalRepository:
    return EmotionalJournalRepository(session)


async def get_mental_alert_repository(
    session: AsyncSession = Depends(get_async_session),
) -> MentalAlertRepository:
    return MentalAlertRepository(session)


async def get_libido_repository(
    session: AsyncSession = Depends(get_async_session),
) -> LibidoRepository:
    return LibidoRepository(session)


async def get_intimate_health_repository(
    session: AsyncSession = Depends(get_async_session),
) -> IntimateHealthRepository:
    return IntimateHealthRepository(session)


async def get_community_post_repository(
    session: AsyncSession = Depends(get_async_session),
) -> CommunityPostRepository:
    return CommunityPostRepository(session)


async def get_community_recipe_repository(
    session: AsyncSession = Depends(get_async_session),
) -> CommunityRecipeRepository:
    return CommunityRecipeRepository(session)


async def get_challenge_repository(
    session: AsyncSession = Depends(get_async_session),
) -> ChallengeRepository:
    return ChallengeRepository(session)


async def get_user_challenge_repository(
    session: AsyncSession = Depends(get_async_session),
) -> UserChallengeRepository:
    return UserChallengeRepository(session)


async def get_consultation_repository(
    session: AsyncSession = Depends(get_async_session),
) -> ConsultationRepository:
    return ConsultationRepository(session)


async def get_chat_repository(
    session: AsyncSession = Depends(get_async_session),
) -> ChatRepository:
    return ChatRepository(session)


# ── Phase 3 — Service providers ──────────────────────────────────────────────


async def get_mental_service(
    session: AsyncSession = Depends(get_async_session),
    moods: MoodRepository = Depends(get_mood_repository),
    journals: EmotionalJournalRepository = Depends(get_emotional_journal_repository),
    alerts: MentalAlertRepository = Depends(get_mental_alert_repository),
    ai_service: AnthropicInsightService | None = Depends(get_anthropic_service),
) -> MentalService:
    return MentalService(
        session=session,
        moods=moods,
        journals=journals,
        alerts=alerts,
        ai_service=ai_service,
    )


async def get_intimate_service(
    session: AsyncSession = Depends(get_async_session),
    libido_repo: LibidoRepository = Depends(get_libido_repository),
    intimate_repo: IntimateHealthRepository = Depends(get_intimate_health_repository),
    ai_service: AnthropicInsightService | None = Depends(get_anthropic_service),
) -> IntimateService:
    return IntimateService(
        session=session,
        libido_repo=libido_repo,
        intimate_repo=intimate_repo,
        ai_service=ai_service,
    )


async def get_community_service(
    session: AsyncSession = Depends(get_async_session),
    posts_repo: CommunityPostRepository = Depends(get_community_post_repository),
    recipes_repo: CommunityRecipeRepository = Depends(get_community_recipe_repository),
    challenges_repo: ChallengeRepository = Depends(get_challenge_repository),
    user_challenges_repo: UserChallengeRepository = Depends(get_user_challenge_repository),
    ai_service: AnthropicInsightService | None = Depends(get_anthropic_service),
) -> CommunityService:
    return CommunityService(
        session=session,
        posts_repo=posts_repo,
        recipes_repo=recipes_repo,
        challenges_repo=challenges_repo,
        user_challenges_repo=user_challenges_repo,
        ai_service=ai_service,
    )


async def get_consultation_service(
    session: AsyncSession = Depends(get_async_session),
    consultation_repo: ConsultationRepository = Depends(get_consultation_repository),
    ai_service: AnthropicInsightService | None = Depends(get_anthropic_service),
) -> ConsultationService:
    return ConsultationService(
        session=session,
        consultation_repo=consultation_repo,
        ai_service=ai_service,
    )


async def get_chat_service(
    session: AsyncSession = Depends(get_async_session),
    chat_repo: ChatRepository = Depends(get_chat_repository),
    ai_service: AnthropicInsightService | None = Depends(get_anthropic_service),
) -> ChatService:
    return ChatService(session=session, chat_repo=chat_repo, ai_service=ai_service)


async def get_dashboard_service(
    session: AsyncSession = Depends(get_async_session),
    user_challenges_repo: UserChallengeRepository = Depends(get_user_challenge_repository),
) -> DashboardService:
    return DashboardService(session=session, user_challenges_repo=user_challenges_repo)


# ── Auth guards ──────────────────────────────────────────────────────────────


async def get_current_user(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    users: UserRepository = Depends(get_user_repository),
) -> User:
    if creds is None:
        raise HTTPException(status_code=401, detail="missing_token")
    payload = decode_token(creds.credentials)
    if payload.get("typ") != "access":
        raise HTTPException(status_code=401, detail="invalid_token")
    sub = payload.get("sub")
    if not isinstance(sub, str):
        raise HTTPException(status_code=401, detail="invalid_token")
    user_id = UUID(sub)
    user = await users.get_active(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="invalid_token")
    request.state.user_id = str(user.id)
    return user


async def require_adult(current_user: User = Depends(get_current_user)) -> User:
    if not is_adult(current_user.date_of_birth):
        raise HTTPException(status_code=403, detail="adult_content_restricted")
    return current_user


async def require_essential(current_user: User = Depends(get_current_user)) -> User:
    if current_user.plan not in (UserPlan.essential, UserPlan.bloom, UserPlan.bloom_pro):
        raise HTTPException(status_code=403, detail="essential_plan_required")
    return current_user


async def require_bloom(current_user: User = Depends(get_current_user)) -> User:
    if current_user.plan not in (UserPlan.bloom, UserPlan.bloom_pro):
        raise HTTPException(status_code=403, detail="bloom_plan_required")
    return current_user


async def require_bloom_pro(current_user: User = Depends(get_current_user)) -> User:
    if current_user.plan != UserPlan.bloom_pro:
        raise HTTPException(status_code=403, detail="bloom_pro_plan_required")
    return current_user


async def require_beta(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.beta_access:
        raise HTTPException(status_code=403, detail="beta_access_required")
    return current_user


async def require_admin(
    request: Request,
) -> None:
    key = request.headers.get("X-Admin-Key", "")
    if not key or key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="admin_access_required")

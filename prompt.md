# FlorNya — Backend Application
## Prompt de base Trae Solo Coder (v1.0)
## Inclut : SOLID + API Best Practices (ByteByteGo)

---

## 0. INSTRUCTIONS TRAE SOLO CODER

Tu es un ingénieur backend senior Python spécialisé en santé numérique.
Avant d'écrire la moindre ligne de code, tu dois :

1. Lire et analyser l'intégralité de ce prompt
2. Générer un plan de développement (PRD technique) ordonné
3. Créer les fichiers de configuration en premier :
   pyproject.toml, .env.example, docker-compose.yml, alembic.ini
4. Générer le code dans cet ordre strict :
   models → schemas → repositories → services → routers → tasks → tests
5. Après chaque module, lancer les tests dans le terminal intégré
6. Ne jamais laisser de `pass` ou `...` sans TODO commenté
7. Valider le démarrage de l'app après chaque étape majeure

### Mode multi-agents recommandé
- Agent 1 : config + models + base SOLID (interfaces, dependencies.py)
- Agent 2 : repositories + services (CycleService, FertilityService, AIService)
- Agent 3 : routers + schemas + pagination + rate limiting
- Agent 4 : tasks Celery + CI/CD + tests

### Commandes de validation par phase
```bash
Phase 1 : docker-compose up -d && alembic upgrade head
Phase 2 : pytest tests/unit/ -v --cov=app
Phase 3 : pytest tests/integration/ -v
Phase 4 : docker-compose -f docker-compose.prod.yml up --build
```

---

## 1. IDENTITÉ & CONTEXTE

**Projet :** FlorNya — Compagne IA de bien-être féminin complet
**Slogan :** "Fleuris à chaque étape."
**Type :** API REST backend FastAPI production-ready
**Domaines couverts :**
  - Cycle menstruel & symptômes
  - Fertilité & conception
  - Grossesse & post-partum
  - Santé hormonale (SOPK, endométriose)
  - Ménopause & périménopause
  - Nutrition féminine & hormones
  - Santé mentale liée aux hormones
  - Bien-être intime & sexualité

**Consommateurs de l'API :**
  - Frontend React PWA (Lovable)
  - Bot Telegram
  - Bot WhatsApp (Twilio)
  - Partenaires B2B (cliniques, gynécologues) — Phase 3

**Contrainte critique :** Les données traitées sont des données de santé
ultra-sensibles (cycle, fertilité, grossesse, dépression post-partum,
santé intime). Toute décision d'architecture doit PRIORITAIREMENT
prendre en compte la sécurité, la confidentialité et la conformité RGPD.
Certaines utilisatrices sont mineures (13+) — protection stricte requise.

---

## 2. STACK TECHNIQUE

```toml
[tool.poetry.dependencies]
python = "^3.11"

# Framework
fastapi = "^0.115"
uvicorn = {extras = ["standard"], version = "^0.30"}
gunicorn = "^22.0"

# Base de données
sqlalchemy = {extras = ["asyncio"], version = "^2.0"}
asyncpg = "^0.29"
alembic = "^1.13"
psycopg2-binary = "^2.9"

# Cache
redis = {extras = ["hiredis"], version = "^5.0"}

# Validation
pydantic = {extras = ["email"], version = "^2.7"}
pydantic-settings = "^2.3"

# Auth
python-jose = {extras = ["cryptography"], version = "^3.3"}
passlib = {extras = ["bcrypt"], version = "^1.7"}
python-multipart = "^0.0.9"

# IA
anthropic = "^0.30"

# Paiements
stripe = "^10.0"

# Messaging
twilio = "^9.0"
python-telegram-bot = "^21.0"

# Email & Push
sendgrid = "^6.11"
firebase-admin = "^6.5"

# Tâches async
celery = {extras = ["redis"], version = "^5.4"}
flower = "^2.0"

# HTTP client
httpx = "^0.27"

# Utilitaires
python-dotenv = "^1.0"
structlog = "^24.0"
sentry-sdk = {extras = ["fastapi"], version = "^2.0"}
slowapi = "^0.1"
cryptography = "^43.0"

# Génération PDF
weasyprint = "^62.0"
jinja2 = "^3.1"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
pytest-asyncio = "^0.23"
pytest-cov = "^5.0"
httpx = "^0.27"
factory-boy = "^3.3"
faker = "^25.0"
ruff = "^0.4"
mypy = "^1.10"
bandit = "^1.7"
pre-commit = "^3.7"
```

---

## 3. ARCHITECTURE DU PROJET

### Structure complète

```
flornya-backend/
├── app/
│   ├── main.py
│   ├── config.py
│   │
│   ├── api/
│   │   ├── deps.py               # Dépendances FastAPI (DIP)
│   │   └── v1/
│   │       ├── router.py
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── cycle.py
│   │       ├── fertility.py
│   │       ├── pregnancy.py
│   │       ├── hormonal.py
│   │       ├── menopause.py
│   │       ├── nutrition.py
│   │       ├── mental.py
│   │       ├── intimate.py
│   │       ├── chat.py
│   │       ├── payments.py
│   │       ├── consultations.py
│   │       └── reports.py
│   │
│   ├── core/
│   │   ├── database.py
│   │   ├── redis.py
│   │   ├── security.py
│   │   ├── exceptions.py
│   │   ├── middleware.py
│   │   └── logging.py
│   │
│   ├── interfaces/               # SOLID — Abstractions (ISP + DIP)
│   │   ├── __init__.py
│   │   ├── ai_provider.py        # IAIProvider, IPlanGenerator, IChatProvider
│   │   ├── notifier.py           # INotifier
│   │   ├── cycle_calculator.py   # ICycleCalculator
│   │   ├── fertility_predictor.py # IFertilityPredictor
│   │   └── storage_provider.py   # IStorageProvider
│   │
│   ├── models/
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── female_profile.py
│   │   ├── cycle_record.py
│   │   ├── symptom_log.py
│   │   ├── mood_log.py
│   │   ├── fertility_record.py
│   │   ├── pregnancy_record.py
│   │   ├── nutrition_plan.py
│   │   ├── food_journal.py
│   │   ├── payment.py
│   │   ├── consultation.py
│   │   └── notification.py
│   │
│   ├── schemas/
│   │   ├── common.py             # PaginatedResponse, CursorPaginatedResponse
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── cycle.py
│   │   ├── fertility.py
│   │   ├── pregnancy.py
│   │   ├── mental.py
│   │   ├── nutrition.py
│   │   └── payment.py
│   │
│   ├── repositories/
│   │   ├── base.py               # BaseRepository CRUD générique
│   │   ├── user_repository.py
│   │   ├── cycle_repository.py
│   │   ├── symptom_repository.py
│   │   ├── mood_repository.py
│   │   ├── fertility_repository.py
│   │   ├── pregnancy_repository.py
│   │   └── nutrition_repository.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── cycle_service.py      # SRP : calculs cycle uniquement
│   │   ├── phase_calculator.py   # SRP : calcul de phase uniquement
│   │   ├── fertility_service.py
│   │   ├── pregnancy_service.py
│   │   ├── mental_service.py
│   │   ├── nutrition_service.py
│   │   ├── payment_service.py
│   │   ├── report_service.py     # Génération PDF
│   │   │
│   │   ├── ai/                   # OCP — providers IA extensibles
│   │   │   ├── anthropic_provider.py
│   │   │   └── openai_provider.py  # Fallback futur
│   │   │
│   │   └── notifications/        # OCP — canaux extensibles
│   │       ├── email_notifier.py
│   │       ├── telegram_notifier.py
│   │       ├── whatsapp_notifier.py
│   │       └── push_notifier.py
│   │
│   └── tasks/
│       ├── celery_app.py
│       ├── reminder_tasks.py     # Rappels cycle, médication
│       ├── epds_tasks.py         # Questionnaire post-partum
│       └── report_tasks.py       # Rapports hebdo PDF
│
├── migrations/
├── tests/
│   ├── conftest.py
│   ├── factories.py
│   ├── unit/
│   └── integration/
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── pyproject.toml
```

---

## 4. CONFIGURATION

```python
# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "FlorNya API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str

    # Base de données
    DATABASE_URL: str           # postgresql+asyncpg://
    DATABASE_URL_SYNC: str      # postgresql:// (Alembic)
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Chiffrement données sensibles
    ENCRYPTION_KEY: str         # Fernet key

    # Anthropic
    ANTHROPIC_API_KEY: str
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    AI_MAX_TOKENS: int = 1500
    AI_TIMEOUT_SECONDS: int = 30

    # Stripe
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_PRICE_ESSENTIEL: str
    STRIPE_PRICE_BLOOM: str
    STRIPE_PRICE_BLOOM_PRO: str

    # Messaging
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_WHATSAPP_NUMBER: str
    TELEGRAM_BOT_TOKEN: str

    # Email & Push
    SENDGRID_API_KEY: str
    FROM_EMAIL: str = "hello@flornya.app"
    FIREBASE_CREDENTIALS_JSON: str

    # Storage
    S3_ENDPOINT_URL: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET_NAME: str = "flornya-uploads"

    # Monitoring
    SENTRY_DSN: str = ""

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]

    # Rate limiting
    RATE_LIMIT_DEFAULT: str = "60/minute"
    RATE_LIMIT_AUTH: str = "10/minute"
    RATE_LIMIT_AI: str = "20/hour"
    RATE_LIMIT_REPORTS: str = "5/day"

    # Protection mineurs
    MINIMUM_AGE: int = 13
    ADULT_CONTENT_AGE: int = 18

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

---

## 5. PRINCIPES SOLID — OBLIGATOIRES

### S — Single Responsibility

Chaque classe a UNE seule responsabilité. Exemples FlorNya :

```python
# ✅ CORRECT
class PhaseCalculator:
    """Calcule uniquement la phase du cycle."""
    def calculate(self, period_start: date, cycle_length: int) -> CyclePhase: ...
    def get_fertile_window(self, ovulation_date: date) -> FertileWindow: ...

class CycleInsightService:
    """Génère uniquement les insights IA sur le cycle."""
    async def generate_insights(self, user_id: UUID, language: str) -> str: ...

class CycleService:
    """Orchestre — ne calcule pas lui-même."""
    def __init__(self, repo: CycleRepository, calculator: PhaseCalculator,
                 insight_svc: CycleInsightService): ...

# ❌ INTERDIT
class CycleService:
    def calculate_phase(self): ...      # ← responsabilité PhaseCalculator
    def generate_insights(self): ...    # ← responsabilité CycleInsightService
    def send_reminder(self): ...        # ← responsabilité NotificationService
```

Checklist SRP FlorNya :
- PhaseCalculator    → calcul phase + fenêtre fertile
- CycleService       → orchestration cycle (appelle PhaseCalculator)
- FertilityService   → fertilité (appelle PhaseCalculator)
- PregnancyService   → grossesse + EPDS uniquement
- MentalService      → humeur + détection SPM/TDPM uniquement
- NutritionService   → plans + recettes (appelle AIService)
- AIService          → appels Anthropic uniquement
- ReportService      → génération PDF uniquement
- PaymentService     → Stripe uniquement
- NotificationService → orchestration canaux (délègue aux notifiers)

### O — Open/Closed

Extensible sans modification. Canaux de notification FlorNya :

```python
# app/interfaces/notifier.py
from abc import ABC, abstractmethod

class INotifier(ABC):
    @abstractmethod
    async def send(self, user_id: str, message: str,
                   payload: dict, language: str = "fr") -> bool: ...

# Implémentations (une par canal)
class EmailNotifier(INotifier): ...
class TelegramNotifier(INotifier): ...
class WhatsAppNotifier(INotifier): ...
class PushNotifier(INotifier): ...
# Demain : SMSNotifier(INotifier) → ZÉRO modif dans NotificationService

class NotificationService:
    def __init__(self, notifiers: list[INotifier]):
        self.notifiers = notifiers   # jamais les implémentations directes

    async def notify_period_incoming(self, user_id: str,
                                     days_before: int, language: str) -> None:
        for notifier in self.notifiers:
            try:
                await notifier.send(user_id, f"Tes règles arrivent dans {days_before}j",
                                    {"type": "period_reminder"}, language)
            except Exception as e:
                logger.error("notifier_failed", notifier=type(notifier).__name__,
                             error=str(e))

# Providers IA extensibles
class IAIProvider(ABC):
    @abstractmethod
    async def generate_nutrition_plan(self, profile: dict, phase: str) -> dict: ...
    @abstractmethod
    async def chat(self, messages: list[dict], system: str) -> str: ...

class AnthropicProvider(IAIProvider): ...
class OpenAIProvider(IAIProvider): ...  # Fallback futur
```

### I — Interface Segregation

Interfaces ciblées, jamais de méthodes inutilisées :

```python
# app/interfaces/cycle_calculator.py
class ICycleCalculator(ABC):
    @abstractmethod
    def calculate_phase(self, period_start: date, cycle_length: int) -> CyclePhase: ...
    @abstractmethod
    def predict_next_period(self, last_period: date, cycle_length: int) -> date: ...
    @abstractmethod
    def get_fertile_window(self, last_period: date, cycle_length: int) -> FertileWindow: ...

# app/interfaces/fertility_predictor.py
class IFertilityPredictor(ABC):
    @abstractmethod
    def calculate_fertility_score(self, bbt: float, mucus: str, lh_result: str) -> int: ...
    @abstractmethod
    def predict_ovulation(self, bbt_history: list[float]) -> date | None: ...

# app/interfaces/ai_provider.py
class IPlanGenerator(ABC):
    @abstractmethod
    async def generate_nutrition_plan(self, profile: dict, phase: str,
                                      preferences: dict) -> dict: ...

class IChatProvider(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict], system: str) -> str: ...

class IPhotoAnalyzer(ABC):
    @abstractmethod
    async def analyze_meal_photo(self, image_base64: str) -> dict: ...

# AnthropicProvider implémente les 3 :
class AnthropicProvider(IPlanGenerator, IChatProvider, IPhotoAnalyzer): ...

# NutritionService n'a besoin que de IPlanGenerator
class NutritionService:
    def __init__(self, ai: IPlanGenerator): ...

# ChatService n'a besoin que de IChatProvider
class ChatService:
    def __init__(self, ai: IChatProvider): ...
```

### D — Dependency Inversion

Tout passe par `app/api/deps.py` via `Depends()` :

```python
# app/api/deps.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_session
from app.interfaces.ai_provider import IPlanGenerator, IChatProvider
from app.services.ai.anthropic_provider import AnthropicProvider
from app.services.notifications.email_notifier import EmailNotifier
from app.services.notifications.push_notifier import PushNotifier

# ─── Providers bas niveau
async def get_ai_provider() -> AnthropicProvider:
    return AnthropicProvider()

async def get_notifiers() -> list[INotifier]:
    return [EmailNotifier(), PushNotifier(), TelegramNotifier()]

# ─── Repositories
async def get_cycle_repository(
    session: AsyncSession = Depends(get_async_session)
) -> CycleRepository:
    return CycleRepository(session)

# ─── Services (dépendent d'abstractions)
async def get_phase_calculator() -> PhaseCalculator:
    return PhaseCalculator()

async def get_cycle_service(
    repo: CycleRepository = Depends(get_cycle_repository),
    calculator: ICycleCalculator = Depends(get_phase_calculator),
    notification_svc: NotificationService = Depends(get_notification_service),
) -> CycleService:
    return CycleService(repository=repo, calculator=calculator,
                        notification=notification_svc)

async def get_nutrition_service(
    repo: NutritionRepository = Depends(get_nutrition_repository),
    ai: IPlanGenerator = Depends(get_ai_provider),
) -> NutritionService:
    return NutritionService(repository=repo, ai=ai)

# ─── Guard plan tarifaire
async def require_bloom(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.plan not in ("bloom", "bloom_pro"):
        raise PaymentRequiredError("Cette fonctionnalité nécessite le plan Bloom")
    return current_user

async def require_bloom_pro(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.plan != "bloom_pro":
        raise PaymentRequiredError("Cette fonctionnalité nécessite Bloom Pro")
    return current_user

async def require_adult(
    current_user: User = Depends(get_current_user)
) -> User:
    age = (date.today() - current_user.date_of_birth).days // 365
    if age < settings.ADULT_CONTENT_AGE:
        raise AgeRestrictionError("Contenu réservé aux 18 ans et plus")
    return current_user
```

---

## 6. API BEST PRACTICES (ByteByteGo)

### B.1 — Clear Naming

```
# Règles FlorNya :
# Ressources au pluriel · Verbes HTTP sémantiques · URLs hiérarchiques

✅ POST   /api/v1/cycle/records               → enregistrer début règles
✅ GET    /api/v1/cycle/current               → phase actuelle
✅ GET    /api/v1/cycle/records               → historique (paginé)
✅ POST   /api/v1/cycle/symptoms              → ajouter symptômes
✅ GET    /api/v1/fertility/window            → fenêtre fertile
✅ POST   /api/v1/fertility/bbt               → température basale
✅ GET    /api/v1/pregnancy/week              → semaine de grossesse
✅ POST   /api/v1/mental/mood                 → humeur du jour
✅ GET    /api/v1/mental/moods                → historique humeurs (paginé)
✅ GET    /api/v1/users/me/female-profile     → profil féminin
✅ GET    /api/v1/reports/pdf                 → rapport médical PDF

❌ GET  /api/v1/getCyclePhase
❌ POST /api/v1/cycle/addSymptom
❌ GET  /api/v1/symptoms?userId=xxx
❌ POST /api/v1/pregnancy/updateWeek
```

### B.2 — Idempotency

```python
# Endpoints critiques avec Idempotency-Key :
# POST /api/v1/payments/subscribe    → abonnement Stripe
# POST /api/v1/nutrition/plans       → génération plan IA
# POST /api/v1/consultations/book    → réservation consultation
# POST /api/v1/reports/pdf           → génération rapport PDF

from fastapi import Header
import json

@router.post("/plans")
@limiter.limit("20/hour")
async def generate_nutrition_plan(
    data: NutritionPlanCreateSchema,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(require_bloom),
    service: NutritionService = Depends(get_nutrition_service),
):
    if idempotency_key:
        cached = await redis_client.get(f"idem:{idempotency_key}")
        if cached:
            return JSONResponse(content=json.loads(cached), status_code=200)

    result = await service.generate_plan(current_user, data)

    if idempotency_key:
        await redis_client.set(f"idem:{idempotency_key}",
                               json.dumps(result.model_dump()), ex=86400)
    return result
```

### B.3 — Pagination

```python
# app/schemas/common.py
from pydantic import BaseModel, Field
from typing import Generic, TypeVar

T = TypeVar("T")

# Offset-based (listes standards)
class PaginationParams(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    skip: int
    limit: int
    has_more: bool

# Cursor-based (historique cycle, humeurs — volumes importants)
class CursorPaginationParams(BaseModel):
    cursor: str | None = Field(default=None)
    limit: int = Field(default=20, ge=1, le=100)

class CursorPaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None
    has_more: bool

# Endpoints utilisant la pagination :
# GET /api/v1/cycle/records      → offset (courte liste)
# GET /api/v1/mental/moods       → cursor (long historique)
# GET /api/v1/cycle/symptoms     → cursor (long historique)
# GET /api/v1/fertility/records  → offset
# GET /api/v1/community/posts    → cursor (feed infini)
```

### B.4 — Sorting & Filtering

```python
# Filtres disponibles par endpoint FlorNya :

# GET /api/v1/cycle/records
class CycleFilterParams(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
    sort_by: str = Field(default="period_start",
                         pattern=r"^(period_start|cycle_length)$")
    order: SortOrder = SortOrder.DESC

# GET /api/v1/mental/moods
class MoodFilterParams(BaseModel):
    period: str | None = Field(default="30d", pattern=r"^\d+[dwm]$")
    min_score: int | None = Field(default=None, ge=1, le=5)
    cycle_phase: CyclePhase | None = None
    sort_by: str = Field(default="log_date")
    order: SortOrder = SortOrder.DESC

# GET /api/v1/cycle/symptoms
class SymptomFilterParams(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
    has_cramps: bool | None = None
    min_energy: int | None = Field(default=None, ge=1, le=5)
    sort_by: str = Field(default="log_date")
    order: SortOrder = SortOrder.DESC

# Exemples d'URLs :
# GET /api/v1/mental/moods?period=30d&min_score=1&cycle_phase=luteal&order=desc
# GET /api/v1/cycle/symptoms?date_from=2026-04-01&has_cramps=true
```

### B.5 — Cross Resource References

```
# URLs hiérarchiques propres :
✅ GET /api/v1/users/me/female-profile
✅ GET /api/v1/users/me/cycle/current
✅ GET /api/v1/consultations/{id}/summary
✅ GET /api/v1/pregnancy/records/{id}/appointments

# Ressource self → /me
✅ GET    /api/v1/users/me
✅ PUT    /api/v1/users/me/settings
✅ DELETE /api/v1/users/me
✅ GET    /api/v1/users/me/data/export

❌ GET /api/v1/cycle/current?user_id=xxx
❌ GET /api/v1/summary?consultation_id=xxx&user_id=xxx
```

### B.6 — Rate Limiting

```python
# Stratégie par endpoint FlorNya :

# Auth (register, login, forgot-password)  → 10/minute par IP
# Endpoints standard (cycle, mood, symptoms) → 60/minute par user_id
# Génération plan nutritionnel IA           → 20/hour par user_id
# Analyse photo repas                       → 10/hour par user_id
# Chat coach IA                             → 30/hour par user_id
# Génération rapport PDF                    → 5/day par user_id
# Export données RGPD                       → 3/day par user_id
# Réservation consultation                  → 10/day par user_id

# Headers obligatoires sur chaque réponse rate-limitée :
# X-RateLimit-Limit: 20
# X-RateLimit-Remaining: 17
# X-RateLimit-Reset: 1714123456
# Retry-After: 3600  (si 429)
```

### B.7 — Versioning

```python
# app/api/v1/router.py
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(auth.router,         prefix="/auth",        tags=["auth"])
api_router.include_router(users.router,        prefix="/users",       tags=["users"])
api_router.include_router(cycle.router,        prefix="/cycle",       tags=["cycle"])
api_router.include_router(fertility.router,    prefix="/fertility",   tags=["fertility"])
api_router.include_router(pregnancy.router,    prefix="/pregnancy",   tags=["pregnancy"])
api_router.include_router(hormonal.router,     prefix="/hormonal",    tags=["hormonal"])
api_router.include_router(menopause.router,    prefix="/menopause",   tags=["menopause"])
api_router.include_router(nutrition.router,    prefix="/nutrition",   tags=["nutrition"])
api_router.include_router(mental.router,       prefix="/mental",      tags=["mental"])
api_router.include_router(intimate.router,     prefix="/intimate",    tags=["intimate"])
api_router.include_router(chat.router,         prefix="/chat",        tags=["chat"])
api_router.include_router(payments.router,     prefix="/payments",    tags=["payments"])
api_router.include_router(consultations.router,prefix="/consultations",tags=["consultations"])
api_router.include_router(reports.router,      prefix="/reports",     tags=["reports"])

# Dans main.py :
# app.include_router(api_router, prefix="/api/v1")

# Politique :
# /api/v1/ → version stable actuelle
# /api/v2/ → uniquement si breaking change majeure
# Dépréciation : header "Sunset: " 6 mois avant suppression
# Header "API-Version: 1.0.0" dans chaque réponse
```

---

## 7. MODÈLES DE DONNÉES (SQLAlchemy 2.0 async)

```python
# app/models/base.py — BaseModel commun
import uuid
from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

class Base(DeclarativeBase): pass

class BaseModel(Base):
    __abstract__ = True
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),
                                           primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  server_default=func.now(),
                                                  onupdate=func.now())
```

### Règles modèles FlorNya
1. Toutes les colonnes médicales sensibles → chiffrées (Fernet AES-128)
   - mood_logs.journal_text
   - symptom_logs.notes
   - fertility_records.bbt_celsius
   - pregnancy_records.epds_score
   - cycle_records.notes
2. users.date_of_birth → obligatoire (vérification d'âge)
3. Soft delete sur users (deleted_at) → jamais de DELETE physique
4. Enum Python pour tous les champs à valeurs fixes
5. Contraintes CHECK au niveau BDD pour toutes les valeurs médicales
6. Index sur (user_id + date) pour toutes les tables de logs
7. Relationship back_populates (jamais backref)

---

## 8. SÉCURITÉ SPÉCIFIQUE FLORNYA

### Protection des mineures
```python
# Middleware de vérification d'âge
async def verify_minimum_age(user: User) -> None:
    age = (date.today() - user.date_of_birth).days // 365
    if age < settings.MINIMUM_AGE:  # 13 ans
        raise HTTPException(403, "Âge minimum requis : 13 ans")

# Guard contenu adulte (18+)
async def require_adult(user: User = Depends(get_current_user)) -> User:
    age = (date.today() - user.date_of_birth).days // 365
    if age < settings.ADULT_CONTENT_AGE:  # 18 ans
        raise AgeRestrictionError()
    return user
```

### Chiffrement journal intime
```python
from cryptography.fernet import Fernet
from app.config import settings

def encrypt_sensitive(value: str) -> str:
    return Fernet(settings.ENCRYPTION_KEY.encode()).encrypt(
        value.encode()).decode()

def decrypt_sensitive(value: str) -> str:
    return Fernet(settings.ENCRYPTION_KEY.encode()).decrypt(
        value.encode()).decode()

# Appliquer sur : journal_text, notes médicales, bbt, epds_score
```

### EPDS — Alerte dépression post-partum
```python
# Seuils Edinburgh Postnatal Depression Scale
EPDS_THRESHOLDS = {
    "normal":  (0, 9),    # < 10 → encouragements
    "watch":   (10, 12),  # 10-12 → ressources bien-être
    "alert":   (13, 30),  # ≥ 13 → orientation professionnelle urgente
}

async def evaluate_epds(score: int, user: User,
                        notification_svc: NotificationService) -> EPDSResult:
    if score >= 13:
        await notification_svc.notify_epds_alert(user, score)
        # Alerte Bloom Pro → gynécologue si consentement donné
    return EPDSResult(score=score, level=get_epds_level(score),
                      resources=get_epds_resources(score, user.language))
```

### Rate limiting & JWT (identique aNihilda)
- bcrypt cost factor 12
- JWT HS256 : access 15min, refresh 30j (révocable)
- 2FA TOTP obligatoire pour Bloom Pro
- Lockout 10 tentatives → 1h
- TLS 1.3 obligatoire
- Zéro PII dans les logs

---

## 9. MODULE IA — ai_service.py

```python
SYSTEM_PROMPT_FLORNYA = """
Tu es FlorNya, une compagne IA de bien-être féminin.
Tu accompagnes les femmes à chaque étape de leur vie.

Langue : {language}
Profil utilisatrice :
- Prénom : {name} | Âge : {age} ans
- Stade de vie : {reproductive_stage}
- Phase cycle : {cycle_phase} (J{cycle_day})
- Conditions de santé : {health_conditions}
- Plan : {plan}

RÈGLES ABSOLUES :
1. Jamais de diagnostic médical
2. Jamais de dosage de médicament
3. Disclaimer médical sur tout conseil de santé
4. Si age < 18 : ton pédagogique, pas de contenu adulte
5. Si stade = postpartum : questionnaire EPDS tous les 15j
6. Si détresse émotionnelle détectée : orienter vers professionnel
"""

class AIService:
    def __init__(self, provider: IAIProvider):  # DIP
        self.provider = provider

    async def generate_nutrition_plan(self, profile: dict,
                                       phase: str, preferences: dict) -> dict:
        """Plan nutritionnel adapté à la phase hormonale."""
        ...

    async def generate_cycle_insights(self, cycle_data: dict,
                                       language: str) -> str:
        """Analyse IA des patterns du cycle."""
        ...

    async def chat(self, message: str, history: list[dict],
                   profile: dict, language: str) -> str:
        """Conversation libre avec le coach."""
        ...

    async def evaluate_mood_journal(self, journal_text: str,
                                     mood_score: int, phase: str,
                                     language: str) -> dict:
        """Analyse bienveillante du journal émotionnel."""
        ...
```

---

## 10. TESTS

### Couverture minimale requise
- PhaseCalculator          : > 98% (calculs critiques)
- CycleService             : > 95%
- PregnancyService (EPDS)  : > 95%
- AuthService              : > 90%
- AIService (mocks)        : 100%
- PaymentService           : > 90%
- Routers                  : > 80%

### Tests critiques FlorNya
```python
# Cycle
def test_phase_calculation_regular_cycle():    # 28j → phases correctes
def test_phase_calculation_short_cycle():      # 21j → phases correctes
def test_fertile_window_accuracy():            # fenêtre ±2j
def test_late_period_detection():              # retard > cycle_length_avg

# Protection mineures
def test_adult_content_blocked_under_18():
def test_minimum_age_13_enforced():
def test_age_appropriate_ai_response():

# EPDS
def test_epds_score_13_triggers_alert():
def test_epds_score_below_10_no_alert():
def test_epds_notification_sent_to_gynecologist():

# Sécurité
def test_journal_text_encrypted_in_db():
def test_bbt_encrypted_in_db():
def test_plan_required_for_bloom_features():
def test_bloom_pro_required_for_consultation():

# IA
def test_medical_disclaimer_present_in_ai_response():
def test_ai_tone_adapted_for_teenager():
def test_ai_mentions_menopause_for_user_over_45():
def test_ai_fallback_if_anthropic_unavailable():

# API Design
def test_pagination_cycle_records():
def test_cursor_pagination_mood_history():
def test_idempotency_key_prevents_duplicate_plan():
def test_rate_limit_ai_endpoints():
def test_sort_filter_symptoms():
```

### conftest.py — fixtures essentielles
```python
@pytest_asyncio.fixture
async def adult_user(user_factory):
    return await user_factory.create(date_of_birth=date(1995, 1, 1))

@pytest_asyncio.fixture
async def teen_user(user_factory):
    return await user_factory.create(date_of_birth=date(2011, 1, 1))

@pytest_asyncio.fixture
async def pregnant_user(user_factory, pregnancy_factory):
    user = await user_factory.create()
    await pregnancy_factory.create(user_id=user.id, mode="pregnancy")
    return user

@pytest_asyncio.fixture
def mock_ai_provider(mocker):
    return mocker.patch("app.services.ai.anthropic_provider.AnthropicProvider")
```

---

## 11. TÂCHES CELERY

```python
# app/tasks/reminder_tasks.py

@celery_app.task
async def send_period_reminder():
    """Chaque matin à 8h — envoyer rappel J-2 avant règles."""
    ...

@celery_app.task
async def send_ovulation_alert():
    """Chaque matin — alerter les utilisatrices en mode conception."""
    ...

@celery_app.task
async def send_mood_checkin():
    """Chaque soir à 20h — rappel de check-in émotionnel."""
    ...

# app/tasks/epds_tasks.py

@celery_app.task
async def send_epds_questionnaire():
    """Tous les 15j pour les utilisatrices en mode postpartum."""
    ...

# app/tasks/report_tasks.py

@celery_app.task
async def generate_weekly_report():
    """Chaque lundi 8h — rapport cycle + humeur de la semaine."""
    ...

@celery_app.task
async def generate_monthly_medical_report():
    """1er de chaque mois — rapport PDF médical (Bloom Pro uniquement)."""
    ...
```

---

## 12. CHECKLIST VALIDATION FINALE

Avant chaque merge, Trae vérifie :

### SOLID
- [ ] SRP : chaque classe a une seule responsabilité
- [ ] OCP : NotificationService et AIService via interfaces (BaseNotifier, IAIProvider)
- [ ] LSP : toutes les sous-classes respectent le contrat parent
- [ ] ISP : IPlanGenerator, IChatProvider, IPhotoAnalyzer séparés
- [ ] DIP : deps.py centralise toutes les injections via Depends()

### API Design
- [ ] URLs snake_case, ressources au pluriel, pas de verbes
- [ ] Idempotency-Key sur /payments, /nutrition/plans, /consultations/book
- [ ] Pagination sur tous les endpoints retournant des listes
- [ ] Filtres et tri sur /cycle/records, /mental/moods, /cycle/symptoms
- [ ] URLs hiérarchiques (/users/me/female-profile, /consultations/{id}/summary)
- [ ] Headers X-RateLimit-* sur tous les endpoints limités
- [ ] Préfixe /api/v1/ sur toutes les routes

### Sécurité FlorNya
- [ ] Vérification d'âge 13+ à l'inscription
- [ ] Contenu 18+ bloqué pour utilisatrices < 18 ans
- [ ] journal_text, bbt, epds_score chiffrés en BDD
- [ ] EPDS ≥ 13 déclenche alerte professionnelle
- [ ] Disclaimer IA présent sur tout conseil médical

### Commandes finales
```bash
pytest tests/ -v --cov=app --cov-fail-under=85
mypy app/ --strict
ruff check app/
bandit -r app/ -ll
uvicorn app.main:app --port 8000 &
curl http://localhost:8000/health
```
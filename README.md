# 🌸 FlorNya API

API backend de **FlorNya**, application de santé féminine complète — suivi de cycle, fertilité, grossesse, santé mentale, nutrition, communauté et bien-être intime.

---

## Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Stack technique](#stack-technique)
- [Fonctionnalités](#fonctionnalités)
- [Plans d'abonnement](#plans-dabonnement)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Base de données](#base-de-données)
- [Lancement](#lancement)
- [Docker](#docker)
- [Architecture](#architecture)
- [Endpoints API](#endpoints-api)
- [Authentification](#authentification)
- [Tâches planifiées (Celery)](#tâches-planifiées-celery)
- [Tests](#tests)
- [Qualité du code](#qualité-du-code)
- [Sécurité](#sécurité)
- [Structure du projet](#structure-du-projet)

---

## Vue d'ensemble

FlorNya est une plateforme de santé féminine qui accompagne les utilisatrices à chaque étape de leur vie reproductive. L'API couvre 4 phases de développement :

| Phase | Domaine | Statut |
|-------|---------|--------|
| 1 | Auth, cycle, humeur, paiements, rappels | ✅ Implémenté |
| 2 | Fertilité, grossesse, santé hormonale, nutrition | ✅ Implémenté |
| 3 | Santé intime, communauté, consultations, chat IA | ✅ Implémenté |
| Extras | Push FCM, upload avatar, Telegram bot, admin | ✅ Implémenté |

---

## Stack technique

| Composant | Technologie |
|-----------|------------|
| Framework | FastAPI 0.115 |
| Langage | Python 3.11 |
| Base de données | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 (async) |
| Cache / Broker | Redis 7 |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Auth | JWT HS256 + TOTP (2FA) |
| Chiffrement | Fernet AES-128 (cryptography) |
| Tâches async | Celery 5 + RedBeat |
| IA | Anthropic Claude (Haiku) |
| Paiements | Stripe |
| Emails | aiosmtplib + Jinja2 |
| Push notifs | Firebase FCM |
| PDF | WeasyPrint + Jinja2 |
| Stockage | AWS S3 (aiobotocore) |
| Bot | Telegram |
| Logs | structlog |
| Rate limiting | SlowAPI |
| Conteneurs | Docker + Docker Compose |

---

## Fonctionnalités

### Authentification & Compte
- Inscription avec vérification de l'âge minimum (13 ans)
- Connexion avec verrouillage après tentatives échouées
- Authentification à deux facteurs TOTP (Google Authenticator, Authy)
- Tokens JWT access (15 min) + refresh (30 jours) rotatifs
- Révocation immédiate à la déconnexion (JTI blacklist Redis)
- Réinitialisation de mot de passe par email (token SHA-256, 1h)
- Export des données personnelles (JSON / CSV) — conformité RGPD
- Suppression de compte avec anonymisation différée (J+30)

### Cycle menstruel
- Enregistrement des cycles (début, fin, intensité du flux)
- Journal de symptômes quotidiens (crampes, fatigue, humeur, énergie…)
- Calendrier mensuel avec phases (menstruelle, folliculaire, ovulatoire, lutéale)
- Prédiction du prochain cycle
- Insights IA personnalisés (Bloom)
- Export PDF du rapport de cycle (Bloom Pro)

### Santé mentale
- Journal d'humeur quotidien avec score et texte libre
- Journal émotionnel avec prompts guidés
- Détection d'alertes de crise mentale
- Analyse de tendances

### Fertilité & Conception
- Suivi de la glaire cervicale et tests LH
- Calendrier de fenêtre fertile
- Suivi de tentatives de conception

### Grossesse
- Profil de grossesse (terme, statut)
- Agenda des rendez-vous médicaux avec rappels J-7 / J-1
- Journal de symptômes de grossesse
- Suivi des séances d'allaitement
- Dépistage EPDS (dépression post-partum)

### Santé hormonale & Douleur
- Suivi des traitements hormonaux (pilule, DIU, patch, injections…)
- Journal de douleur pelvienne et endométriose
- Rapport médical PDF exportable pour consultations

### Ménopause & Périménopause
- Journal des symptômes (bouffées, sueurs nocturnes, insomnie)
- Statistiques et rapport médical PDF

### Nutrition
- Journal alimentaire quotidien
- Score nutritionnel

### Santé intime
- Suivi libido et satisfaction intime
- Journal de santé vaginale (pertes, inconfort)

### Communauté
- Posts et forum (catégorisés)
- Recettes santé féminine
- Défis bien-être et suivi de progression

### Consultations
- Réservation de consultations avec professionnels
- Statuts : pending → confirmed → completed / cancelled

### Chat IA
- Chat contextuel avec Claude (Anthropic)
- Historique de conversation persisté

### Notifications
- Push notifications Firebase FCM (iOS / Android)
- Rappels : règles, médicaments, hydratation, check-in humeur, rendez-vous
- Emails transactionnels : bienvenue, reset mot de passe, rappel de période, confirmation d'abonnement

### Paiements
- Intégration Stripe (checkout, portal client, webhooks)
- Factures stockées et consultables
- Mise à jour automatique du plan après paiement

### Administration
- Gestion des plans utilisateurs
- Activation/désactivation de l'accès beta
- Suppression définitive d'un compte
- Toutes les actions sont auditées (structlog)

---

## Plans d'abonnement

| Plan | Accès |
|------|-------|
| `free` | Compte uniquement |
| `essential` | Cycle, symptômes, humeur, rappels |
| `bloom` | Essential + insights IA, calendrier fertilité |
| `bloom_pro` | Bloom + export PDF, assistance prioritaire |

Les guards `require_essential`, `require_bloom`, `require_bloom_pro` protègent les endpoints correspondants.

---

## Prérequis

- Python **3.11+**
- PostgreSQL **16+**
- Redis **7+**
- Poetry (`pip install poetry`)
- Docker & Docker Compose (optionnel)

---

## Installation

```bash
# Cloner le dépôt
git clone https://github.com/flornya/flornya-api.git
cd flornya-api

# Installer les dépendances
poetry install

# Copier la configuration
cp .env.example .env
```

Éditer `.env` avec vos valeurs (voir [Configuration](#configuration)).

---

## Configuration

Toutes les variables d'environnement sont dans `.env`. Voici les groupes essentiels :

### Application

```env
APP_NAME="FlorNya API"
ENVIRONMENT=development        # development | production
DEBUG=false
SECRET_KEY=<openssl rand -hex 32>
```

> **Important :** L'application refuse de démarrer si `SECRET_KEY` est une valeur par défaut.

### Base de données

```env
DATABASE_URL=postgresql+asyncpg://flornya:flornya@localhost:5432/flornya
DATABASE_URL_SYNC=postgresql://flornya:flornya@localhost:5432/flornya
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

### Redis

```env
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
```

### JWT & Chiffrement

```env
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# Générer avec : python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=<votre-clé-fernet>
```

### Email SMTP

Le service email fonctionne avec n'importe quel provider SMTP. Laisser `SMTP_HOST` vide active le mode stub (logs console).

```env
SMTP_HOST=smtp.resend.com      # ou smtp.sendgrid.net, smtp.mailgun.org, smtp.gmail.com…
SMTP_PORT=587
SMTP_TLS_MODE=starttls         # starttls (port 587) | ssl (port 465) | none
SMTP_USER=resend
SMTP_PASSWORD=re_xxxx
EMAIL_FROM=noreply@flornya.app
FRONTEND_URL=https://app.flornya.app
PASSWORD_RESET_EXPIRE_MINUTES=60
```

### Stripe

```env
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ESSENTIAL=price_...
STRIPE_PRICE_BLOOM=price_...
STRIPE_PRICE_BLOOM_PRO=price_...
```

### Anthropic (Claude AI)

```env
ANTHROPIC_API_KEY=sk-ant-...
AI_INSIGHTS_MODEL=claude-haiku-4-5-20251001
```

### Firebase FCM (push notifications)

```env
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
FIREBASE_PROJECT_ID=flornya-prod
```

> Télécharger le fichier JSON depuis Firebase Console → Paramètres → Comptes de service.  
> Laisser vide : le service bascule en mode stub (logs console).

### Upload Avatar (AWS S3)

```env
S3_BUCKET_NAME=flornya-avatars
S3_REGION=eu-west-3
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AVATAR_MAX_SIZE_MB=5
```

> Laisser vide : l'avatar est stocké en base64 (développement uniquement).

### Administration

```env
# Générer avec : openssl rand -hex 32
ADMIN_API_KEY=<clé-admin>
```

Passer dans le header `X-Admin-Key` pour accéder aux endpoints `/admin/*`.

### Telegram Bot

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdef...
TELEGRAM_WEBHOOK_SECRET=<chaîne-aléatoire>
```

### CORS

```env
ALLOWED_ORIGINS=["http://localhost:5173","https://app.flornya.app"]
```

---

## Base de données

### Créer la base

```bash
createdb flornya
```

### Appliquer les migrations

```bash
poetry run alembic upgrade head
```

### Créer une nouvelle migration

```bash
poetry run alembic revision --autogenerate -m "description"
```

### Historique des migrations

| Révision | Contenu |
|----------|---------|
| `0001_initial` | Schéma initial — User, FemaleProfile, CycleRecord, MoodLog |
| `0002_phase1` | Auth avancée, StripeInvoice, ReminderConfig, SymptomLog |
| `0003_phase2` | Fertilité, grossesse, hormones, nutrition |
| `0004_phase3` | Communauté, consultations, chat, santé intime |
| `0005_extras` | DeviceToken, enum `essential` dans UserPlan |

---

## Lancement

### Développement

```bash
# Démarrer PostgreSQL et Redis (si non dockerisés)
brew services start postgresql redis  # macOS

# Lancer l'API
poetry run uvicorn app.main:app --reload --port 8000

# Lancer le worker Celery (terminal séparé)
poetry run celery -A app.celery_app worker --loglevel=info

# Lancer le scheduler Celery Beat (terminal séparé)
poetry run celery -A app.celery_app beat --scheduler redbeat.RedBeatScheduler --loglevel=info
```

L'API est disponible sur : `http://localhost:8000`  
Documentation Swagger : `http://localhost:8000/docs`  
Documentation ReDoc : `http://localhost:8000/redoc`

### Production

```bash
poetry run gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  -w 4 \
  --bind 0.0.0.0:8000
```

---

## Docker

### Démarrer tous les services

```bash
docker-compose up -d
```

Cela lance :
- `postgres` — PostgreSQL 16 (port 5432)
- `redis` — Redis 7 (port 6379)
- `api` — FastAPI (port 8000)
- `celery_worker` — Worker Celery (concurrency 4)
- `celery_beat` — Scheduler RedBeat

### Appliquer les migrations en Docker

```bash
docker-compose exec api alembic upgrade head
```

### Logs

```bash
docker-compose logs -f api
docker-compose logs -f celery_worker
```

### Arrêter

```bash
docker-compose down
# Supprimer aussi les volumes (reset complet)
docker-compose down -v
```

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Client (Frontend)                │
└──────────────────────┬──────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────┐
│               FastAPI (app/main.py)                 │
│  CORSMiddleware · SecurityHeaders · RateLimiting    │
├─────────────────────────────────────────────────────┤
│            Routers (app/api/v1/)                    │
│  auth · users · cycle · mental · fertility          │
│  pregnancy · hormonal · menopause · nutrition       │
│  intimate · community · consultation · chat         │
│  payments · reminders · dashboard · admin · bot     │
├─────────────────────────────────────────────────────┤
│   Dependency Injection (app/api/deps.py)            │
│   JWT validation · plan guards · service factories  │
├──────────────┬──────────────────────────────────────┤
│   Services   │          Repositories                │
│  (business   │       (data access layer)            │
│   logic)     │                                      │
├──────────────┴──────────────────────────────────────┤
│         SQLAlchemy AsyncSession (PostgreSQL)         │
├─────────────────────────────────────────────────────┤
│                Redis                                │
│  Access token blacklist · Refresh JTI store         │
│  Login attempts · Celery broker                     │
├──────────────────────┬──────────────────────────────┤
│    Celery Worker     │       Celery Beat             │
│  (async tasks)       │  (scheduled tasks)            │
└──────────────────────┴──────────────────────────────┘
```

### Couches applicatives

| Couche | Rôle |
|--------|------|
| `app/api/v1/` | Endpoints FastAPI — validation HTTP, codes de statut |
| `app/api/deps.py` | Injection de dépendances — auth, guards de plan, sessions |
| `app/services/` | Logique métier — règles, calculs, orchestration |
| `app/repositories/` | Accès données — queries SQLAlchemy |
| `app/models/` | Modèles SQLAlchemy — définition des tables |
| `app/schemas/` | Schémas Pydantic — validation des requêtes/réponses |
| `app/core/` | Infrastructure — DB, Redis, sécurité, middleware, logs |

---

## Endpoints API

Base URL : `/api/v1`

### Authentification (`/auth`)

| Méthode | Endpoint | Description | Auth |
|---------|----------|-------------|------|
| `POST` | `/auth/register` | Créer un compte | Non |
| `POST` | `/auth/login` | Connexion | Non |
| `POST` | `/auth/refresh` | Rafraîchir les tokens | Non |
| `POST` | `/auth/logout` | Déconnexion + révocation | Oui |
| `POST` | `/auth/password-reset/request` | Demander un reset | Non |
| `POST` | `/auth/password-reset/confirm` | Confirmer le reset | Non |
| `POST` | `/auth/2fa/setup` | Configurer le TOTP | Oui |
| `POST` | `/auth/2fa/confirm` | Activer le TOTP | Oui |
| `POST` | `/auth/2fa/verify` | Vérifier le code TOTP | Non |
| `DELETE` | `/auth/2fa` | Désactiver le TOTP | Oui |

### Utilisateurs (`/users`)

| Méthode | Endpoint | Description | Plan |
|---------|----------|-------------|------|
| `GET` | `/users/me` | Profil courant | Tous |
| `PATCH` | `/users/me` | Modifier le profil | Tous |
| `POST` | `/users/me/onboarding` | Compléter l'onboarding | Tous |
| `PATCH` | `/users/me/extended-profile` | Mettre à jour le profil étendu | Tous |
| `GET` | `/users/me/female-profile` | Profil féminin | Tous |
| `PUT` | `/users/me/female-profile` | Upsert profil féminin | Tous |
| `POST` | `/users/me/avatar` | Upload photo de profil | Tous |
| `GET` | `/users/me/export` | Export RGPD (JSON/CSV) | Tous |
| `DELETE` | `/users/me` | Supprimer le compte | Tous |
| `POST` | `/users/me/device-token` | Enregistrer token FCM | Tous |
| `DELETE` | `/users/me/device-token` | Désactiver token FCM | Tous |
| `POST` | `/users/me/beta-activate` | Activer l'accès beta | Tous |

### Cycle (`/cycle`)

| Méthode | Endpoint | Description | Plan |
|---------|----------|-------------|------|
| `GET` | `/cycle/records` | Historique des cycles | Essential+ |
| `POST` | `/cycle/records` | Enregistrer un cycle | Essential+ |
| `GET` | `/cycle/calendar` | Calendrier mensuel | Essential+ |
| `POST` | `/cycle/symptoms` | Logger les symptômes | Essential+ |
| `GET` | `/cycle/symptoms` | Historique symptômes | Essential+ |
| `GET` | `/cycle/insights` | Insights IA | Bloom+ |
| `GET` | `/cycle/export/pdf` | Export PDF | Bloom Pro |

### Santé mentale (`/mental`)

| Méthode | Endpoint | Description | Plan |
|---------|----------|-------------|------|
| `POST` | `/mental/mood` | Logger l'humeur | Essential+ |
| `GET` | `/mental/moods` | Historique humeurs | Essential+ |
| `POST` | `/mental/journal` | Entrée de journal | Essential+ |
| `GET` | `/mental/journals` | Historique journal | Essential+ |
| `GET` | `/mental/alerts` | Alertes actives | Essential+ |

### Fertilité (`/fertility`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/fertility/log` | Logger données de fertilité |
| `GET` | `/fertility/logs` | Historique fertilité |
| `GET` | `/fertility/window` | Fenêtre fertile prévue |
| `POST` | `/fertility/conception` | Logger tentative de conception |

### Grossesse (`/pregnancy`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/pregnancy/profile` | Profil de grossesse |
| `PUT` | `/pregnancy/profile` | Mettre à jour le profil |
| `GET` | `/pregnancy/appointments` | Rendez-vous médicaux |
| `POST` | `/pregnancy/appointments` | Créer un rendez-vous |
| `DELETE` | `/pregnancy/appointments/{id}` | Supprimer un rendez-vous |
| `POST` | `/pregnancy/symptoms` | Logger symptômes |
| `POST` | `/pregnancy/breastfeeding` | Logger allaitement |
| `POST` | `/pregnancy/epds` | Évaluation EPDS |

### Santé hormonale (`/hormonal-health`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/hormonal-health/treatments` | Traitements en cours |
| `POST` | `/hormonal-health/treatments` | Ajouter un traitement |
| `POST` | `/hormonal-health/pain` | Logger une douleur |
| `GET` | `/hormonal-health/pain` | Historique douleurs |
| `GET` | `/hormonal-health/export/pdf` | Rapport douleur PDF |

### Ménopause (`/menopause`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/menopause/log` | Logger symptômes ménopause |
| `GET` | `/menopause/logs` | Historique |
| `GET` | `/menopause/export/pdf` | Rapport PDF |

### Nutrition (`/nutrition`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/nutrition/log` | Logger un repas |
| `GET` | `/nutrition/logs` | Historique nutritionnel |

### Santé intime (`/intimate`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/intimate/libido` | Logger libido |
| `POST` | `/intimate/health` | Logger santé intime |
| `GET` | `/intimate/history` | Historique |

### Communauté (`/community`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/community/posts` | Liste des posts |
| `POST` | `/community/posts` | Créer un post |
| `GET` | `/community/recipes` | Recettes santé |
| `POST` | `/community/recipes` | Partager une recette |
| `GET` | `/community/challenges` | Défis disponibles |
| `POST` | `/community/challenges/{id}/join` | Rejoindre un défi |

### Consultations (`/consultation`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/consultation/bookings` | Mes réservations |
| `POST` | `/consultation/bookings` | Réserver une consultation |
| `PATCH` | `/consultation/bookings/{id}` | Modifier le statut |

### Chat IA (`/chat`)

| Méthode | Endpoint | Description | Limite |
|---------|----------|-------------|--------|
| `POST` | `/chat/message` | Envoyer un message à Claude | 20/heure |
| `GET` | `/chat/history` | Historique de la conversation | — |

### Paiements (`/payments`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/payments/checkout` | Créer une session Stripe |
| `POST` | `/payments/portal` | Portail client Stripe |
| `POST` | `/payments/webhook` | Webhook Stripe (sans auth) |
| `GET` | `/payments/invoices` | Mes factures |

### Rappels (`/reminders`)

| Méthode | Endpoint | Description | Plan |
|---------|----------|-------------|------|
| `GET` | `/reminders` | Mes rappels configurés | Essential+ |
| `PUT` | `/reminders/{type}` | Configurer un rappel | Essential+ |
| `DELETE` | `/reminders/{type}` | Supprimer un rappel | Essential+ |

Types : `period`, `medication`, `hydration`, `mood_checkin`

### Dashboard (`/dashboard`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/dashboard` | Données synthétiques du tableau de bord |

### Administration (`/admin`)

> Header requis : `X-Admin-Key: <ADMIN_API_KEY>`

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/admin/users` | Liste des utilisateurs |
| `PATCH` | `/admin/users/{id}/plan` | Modifier le plan |
| `PATCH` | `/admin/users/{id}/beta` | Activer/désactiver beta |
| `DELETE` | `/admin/users/{id}` | Supprimer définitivement |

### Bot (`/bot`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/bot/telegram/webhook` | Webhook Telegram |

### Santé

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/health` | Statut du serveur |

---

## Authentification

### Flux standard

```
POST /auth/register  →  { access_token, refresh_token }
POST /auth/login     →  { access_token, refresh_token }
                         ou { requires_2fa: true, challenge_token }
POST /auth/2fa/verify  →  { access_token, refresh_token }
POST /auth/refresh   →  { access_token, refresh_token }
POST /auth/logout    →  204
```

### Header d'autorisation

```
Authorization: Bearer <access_token>
```

### Tokens

| Token | Durée | Stockage Redis |
|-------|-------|---------------|
| Access | 15 min | JTI blacklisté à la déconnexion |
| Refresh | 30 jours | JTI stocké, rotation à chaque refresh |
| 2FA challenge | 5 min | JWT autonome |
| Reset password | 1 heure | Hash SHA-256 en base de données |

---

## Tâches planifiées (Celery)

| Tâche | Planning | Description |
|-------|----------|-------------|
| `send_period_reminders` | Toutes les heures | Push + email J-N avant les règles |
| `send_medication_reminders` | Toutes les heures | Rappel médicament à l'heure configurée |
| `send_hydration_reminders` | 8h, 11h, 14h, 17h, 20h UTC | Rappel hydratation |
| `send_mood_checkin_reminders` | Toutes les heures | Check-in si pas encore loggé |
| `send_pregnancy_appointment_reminders` | 8h UTC | Rappels J-7 et J-1 avant RDV |
| `anonymize_pending_deletions` | 3h UTC | Anonymise les comptes supprimés depuis 30j |

### Lancer une tâche manuellement

```bash
poetry run celery -A app.celery_app call \
  app.tasks.reminder_tasks.send_period_reminders
```

---

## Tests

### Lancer les tests

```bash
# Tous les tests
poetry run pytest

# Avec couverture
poetry run pytest --cov=app --cov-report=html

# Un module spécifique
poetry run pytest tests/integration/test_auth.py -v

# Un test spécifique
poetry run pytest tests/integration/test_auth.py::test_register -v
```

### Configuration des tests

Les tests utilisent :
- **SQLite en mémoire** (aiosqlite) — pas besoin de PostgreSQL
- **FakeRedis** — pas besoin de Redis
- **AsyncClient** (httpx) — requêtes HTTP complètes

```python
# Helpers courants dans les tests
async def _set_plan(db, user_id, plan):
    """Élever un utilisateur à un plan supérieur."""
```

### Structure des tests

```
tests/
├── conftest.py                  # Fixtures partagées (app, client, DB, user)
└── integration/
    ├── test_auth.py             # Auth, 2FA, reset mot de passe
    ├── test_users.py            # Profil, onboarding, RGPD
    ├── test_phase1_features.py  # Cycle, symptômes, rappels
    ├── test_phase2_features.py  # Fertilité, grossesse, hormones
    ├── test_phase3_features.py  # Communauté, chat, consultations
    └── test_extras_features.py  # Beta, device tokens, avatar, Telegram
```

---

## Qualité du code

```bash
# Linting
poetry run ruff check app/

# Formatage (vérification)
poetry run ruff format --check app/

# Type checking
poetry run mypy app/ --strict

# Sécurité statique
poetry run bandit -r app/ -ll
```

Configuration dans `pyproject.toml` :
- **Ruff** : longueur 100, règles E/F/I/B/UP, cible Python 3.11
- **MyPy** : mode strict, exclut `migrations/`

---

## Sécurité

| Mesure | Implémentation |
|--------|---------------|
| Secrets JWT | HS256 + `token_version` pour révocation de masse |
| Révocation unitaire | JTI blacklist Redis (TTL = durée restante du token) |
| Chiffrement données sensibles | Fernet AES-128 (clé en env, jamais en DB) |
| Tokens de reset | SHA-256 stocké — le token brut n'est jamais persisté |
| Verrouillage login | Blocage après 10 tentatives / 1 heure (Redis) |
| Validation images | Magic bytes (JPEG/PNG/WebP) + suppression EXIF (Pillow) |
| CORS restreint | Méthodes et headers explicitement listés |
| Headers sécurité | HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy |
| Admin timing-safe | `secrets.compare_digest` contre les attaques temporelles |
| Webhook Stripe | Vérification signature + tolérance timestamp 5 min |
| Webhook Telegram | `X-Telegram-Bot-Api-Secret-Token` (HMAC) |
| Âge minimum | Calcul précis via `dateutil.relativedelta` |
| Démarrage sécurisé | Rejet si `SECRET_KEY` est une valeur par défaut connue |

---

## Structure du projet

```
flornya-api/
├── app/
│   ├── main.py                   # Point d'entrée FastAPI
│   ├── config.py                 # Variables d'environnement (Pydantic Settings)
│   ├── celery_app.py             # Configuration Celery + schedule Beat
│   │
│   ├── api/
│   │   ├── deps.py               # Injection de dépendances + guards de plan
│   │   └── v1/
│   │       ├── router.py         # Agrégateur de routes
│   │       ├── auth.py           # Auth, 2FA, reset mot de passe
│   │       ├── users.py          # Profil, onboarding, avatar, RGPD
│   │       ├── cycle.py          # Cycle menstruel, symptômes, PDF
│   │       ├── mental.py         # Humeur, journal, alertes
│   │       ├── fertility.py      # Fertilité, LH, conception
│   │       ├── pregnancy.py      # Grossesse, RDV, allaitement, EPDS
│   │       ├── hormonal_health.py# Traitements, douleur, PDF
│   │       ├── menopause.py      # Ménopause, PDF
│   │       ├── nutrition.py      # Journal alimentaire
│   │       ├── intimate.py       # Libido, santé vaginale
│   │       ├── community.py      # Posts, recettes, défis
│   │       ├── consultation.py   # Réservations
│   │       ├── chat.py           # Chat Claude IA
│   │       ├── dashboard.py      # Tableau de bord
│   │       ├── payments.py       # Stripe, factures
│   │       ├── reminders.py      # Configuration rappels
│   │       ├── admin.py          # Admin (X-Admin-Key)
│   │       └── bot.py            # Webhook Telegram
│   │
│   ├── models/                   # 32 modèles SQLAlchemy
│   ├── repositories/             # 22 repositories (accès données)
│   ├── schemas/                  # Schémas Pydantic (validation)
│   ├── services/                 # 22 services (logique métier)
│   ├── interfaces/               # Interfaces abstraites (SOLID)
│   ├── bot/                      # Telegram bot handler
│   ├── tasks/                    # Tâches Celery
│   │   ├── reminder_tasks.py     # Rappels planifiés
│   │   └── account_tasks.py     # Anonymisation
│   ├── core/
│   │   ├── database.py           # SQLAlchemy async engine
│   │   ├── redis.py              # Client Redis
│   │   ├── security.py           # JWT, Fernet, hashing, image utils
│   │   ├── middleware.py         # Rate limiting, API version header
│   │   └── logging.py            # structlog
│   └── templates/
│       ├── email/                # Templates Jinja2 (bienvenue, reset, rappels)
│       │   ├── base.css          # CSS partagé (injecté via {% include %})
│       │   ├── base.html         # Layout de base
│       │   ├── welcome.html
│       │   ├── password_reset.html
│       │   ├── period_reminder.html
│       │   └── subscription_confirmed.html
│       └── pdf/                  # Templates WeasyPrint
│           ├── base.css          # CSS partagé PDF
│           ├── cycle_report.html / .css
│           ├── monthly_report.html / .css
│           ├── pain_report.html / .css
│           └── menopause_report.html / .css
│
├── migrations/
│   ├── env.py
│   └── versions/
│       ├── 0001_initial.py
│       ├── 0002_phase1.py
│       ├── 0003_phase2.py
│       ├── 0004_phase3.py
│       └── 0005_extras.py
│
├── tests/
│   ├── conftest.py
│   └── integration/
│
├── .env.example                  # Référence de configuration complète
├── docker-compose.yml            # Orchestration Docker
├── Dockerfile
├── pyproject.toml                # Dépendances + config outils
└── alembic.ini
```

---

## Licence

Propriétaire — © 2026 FlorNya. Tous droits réservés.

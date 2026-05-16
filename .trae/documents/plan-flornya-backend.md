# Plan de développement — FlorNya (backend FastAPI)

## Summary
Objectif : transformer le projet actuel (un `main.py` minimal FastAPI à la racine) en une API REST **production‑ready** conforme au prompt [prompt.md](file:///n:/OneDrive%20-%20Universit%C3%A9%20Cheikh%20Anta%20DIOP%20de%20DAKAR/PycharmProjects/FlorNya/prompt.md), avec :
- structure `app/` modulaire (models → schemas → repositories → services → routers → tasks → tests)
- PostgreSQL async + Alembic, Redis, rate limiting, sécurité (JWT, mineures 13+, chiffrement champs sensibles)
- points d’entrée API versionnés `/api/v1`
- base de tests + CI locale (ruff/mypy/bandit) et validation du démarrage.

## Current State Analysis
- Le dépôt ne contient que :
  - [main.py](file:///n:/OneDrive%20-%20Universit%C3%A9%20Cheikh%20Anta%20DIOP%20de%20DAKAR/PycharmProjects/FlorNya/main.py) : app FastAPI avec 2 endpoints (`/`, `/hello/{name}`)
  - [test_main.http](file:///n:/OneDrive%20-%20Universit%C3%A9%20Cheikh%20Anta%20DIOP%20de%20DAKAR/PycharmProjects/FlorNya/test_main.http)
  - [.gitignore](file:///n:/OneDrive%20-%20Universit%C3%A9%20Cheikh%20Anta%20DIOP%20de%20DAKAR/PycharmProjects/FlorNya/.gitignore)
- Absents : `pyproject.toml`, `.env.example`, `docker-compose.yml`, `alembic.ini`, répertoire `app/`, tests, migrations, etc.
- Une `.venv/` est présente localement, mais n’est pas une source de vérité projet (elle sera ignorée par git).

## Assumptions & Decisions
- Périmètre retenu : **MVP A** (Auth + Users + Cycle + Mental).
- Hors scope immédiat (reporté) : IA (Anthropic), Nutrition, Paiements Stripe, Messaging (Twilio/Telegram), Rapports PDF, tâches Celery.
- Packaging : **Poetry** via `pyproject.toml` (tel que défini dans le prompt).
- DB : **PostgreSQL** en local via `docker-compose.yml` + `asyncpg` (runtime) et `psycopg2-binary` (alembic sync).
- Cache/rate limiting : **Redis** en local via docker-compose.
- API : préfixe global `/api/v1`, router agrégateur `app/api/v1/router.py`, endpoints “resources-first”.
- Sécurité :
  - JWT HS256 (access 15min, refresh 30j) et hashing bcrypt (cost 12).
  - Vérification âge minimum 13+ (inscription), blocage contenu adulte < 18.
  - Chiffrement applicatif (Fernet) pour champs médicaux sensibles listés dans le prompt.
  - Zéro PII dans les logs.
- Stratégie de livraison : construire d’abord un “vertical slice” (config + DB + auth + users + cycle minimal) puis étendre module par module, en conservant le même squelette SOLID/DIP.

## Proposed Changes (ordre strict)

### 1) Configuration & squelette projet (fichiers racine en premier)
Créer/mettre à jour :
- `pyproject.toml`
  - dépendances Poetry selon la section “STACK TECHNIQUE” du prompt
  - configuration ruff + mypy (strict) + pytest
- `.env.example`
  - toutes les variables listées dans `Settings` (SECRET_KEY, DATABASE_URL, DATABASE_URL_SYNC, ENCRYPTION_KEY, clés providers, etc.)
  - valeurs de dev non sensibles (ex : `ENVIRONMENT=development`) et placeholders pour secrets
- `docker-compose.yml`
  - services : `postgres` + `redis`
  - volumes persistants + ports standards
- `alembic.ini` + répertoire `migrations/`
  - Alembic configuré sur `DATABASE_URL_SYNC`
- `Dockerfile` (dev/prod basique) aligné sur Poetry

Restructurer le code :
- Créer le package `app/` et déplacer l’actuel `main.py` vers `app/main.py`
- Ajouter `app/config.py` (Settings Pydantic v2 comme dans le prompt)
- Ajouter `app/core/` (base : `database.py`, `redis.py`, `logging.py`, `exceptions.py`, `security.py`, `middleware.py`)
- Ajouter un endpoint `GET /health` (utilisé par la checklist finale du prompt)

### 2) Models (SQLAlchemy 2.0 async)
Créer :
- `app/models/base.py` (Base + BaseModel id/created_at/updated_at)
- `app/models/user.py` (soft delete `deleted_at`, date_of_birth obligatoire, plan, langue, etc.)
- `app/models/female_profile.py` (profil féminin)
- `app/models/cycle_record.py`, `symptom_log.py`, `mood_log.py` (index `(user_id, date)`, champs sensibles chiffrés)

Décisions techniques dans les modèles :
- Utiliser `Enum` Python pour les champs à valeurs fixes (phase cycle, plan, etc.)
- Contraintes CHECK au niveau SQLAlchemy (et donc migrées via Alembic)
- Aucun `backref`, uniquement `back_populates`

### 3) Schemas (Pydantic v2)
Créer :
- `app/schemas/common.py` (Pagination offset + cursor, paramètres filtres/tri communs)
- `app/schemas/auth.py`, `user.py`, `cycle.py`, `mental.py`, etc. (au minimum auth/users/cycle pour démarrer)

### 4) Repositories
Créer :
- `app/repositories/base.py` (CRUD générique, helpers pagination, filtres/tri)
- `app/repositories/user_repository.py`
- `app/repositories/cycle_repository.py`
- `app/repositories/symptom_repository.py`
- `app/repositories/mood_repository.py`

### 5) Services (SOLID)
Créer :
- `app/services/auth_service.py` (register/login/refresh, lockout 10 tentatives, hashing)
- `app/services/user_service.py` (profil, export RGPD)
- `app/services/phase_calculator.py` (calcul phase + fenêtre fertile — testé à >98%)
- `app/services/cycle_service.py` (orchestration : repo + calculator + notifications)
- `app/services/mental_service.py` (moods + règles mineures)

Chiffrement :
- Centraliser `encrypt_sensitive/decrypt_sensitive` dans `app/core/security.py` (ou `app/core/crypto.py`) et l’utiliser dans les services/repositories (pas dans les routers).

### 6) Routers (API v1)
Créer :
- `app/api/deps.py` : point central DIP (sessions DB, repositories, services, guards plan, guards âge)
- `app/api/v1/router.py` : agrégateur v1
- Routers v1 initiaux :
  - `app/api/v1/auth.py` : register/login/refresh
  - `app/api/v1/users.py` : `/users/me`, `/users/me/female-profile`, settings
  - `app/api/v1/cycle.py` : records + current phase + symptoms (avec pagination/filtres)
  - `app/api/v1/mental.py` : mood logs (cursor pagination)

Cross-cutting :
- Rate limiting (slowapi) appliqué par endpoint selon la table du prompt
- Headers `API-Version` + `X-RateLimit-*` sur réponses concernées

### 7) Tests
Créer structure :
- `tests/conftest.py` (fixtures async : session DB, factories, utilisateurs adult/teen/pregnant)
- `tests/unit/` :
  - `test_phase_calculator.py` (cas 21j, 28j, fenêtre fertile, retard)
  - `test_security_age.py` (13+, 18+)
  - `test_encryption.py` (journal_text, bbt, epds_score chiffrés)
- `tests/integration/` :
  - auth flow
  - endpoints paginés + cursor pagination
  - rate limit sur endpoints auth (quand applicable) + endpoints standards

Objectif de couverture :
- global : `--cov-fail-under=85` (comme checklist)
- ciblé : respecter les seuils indiqués dans le prompt là où applicable

## Verification Steps (local)
Validation “phase par phase” (sans exécuter ici, juste la liste des checks à faire pendant l’implémentation) :
1. Démarrage infra : `docker-compose up -d`
2. Migrations : `alembic upgrade head`
3. Tests unitaires : `pytest tests/unit/ -v --cov=app`
4. Tests intégration : `pytest tests/integration/ -v`
5. Qualité : `ruff check app/` puis `mypy app/ --strict` puis `bandit -r app/ -ll`
6. Run app : `uvicorn app.main:app --port 8000`
7. Smoke : `GET /health` retourne 200

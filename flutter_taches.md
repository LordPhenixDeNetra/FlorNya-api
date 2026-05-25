# FlorNya — Tâches Flutter (implémentation de l’API)

## Légende des statuts

- **À faire** : pas démarré
- **En cours** : développement actif
- **Bloqué** : dépendance / décision manquante
- **Fait** : terminé

## Liste à cocher

- Cocher = **Fait**

### À faire

**Base app & architecture**
- [ ] **(Flutter · P0)** Setup projet — conventions, lint, routing, DI, environnements (dev/staging/prod)
- [ ] **(Flutter · P0)** Configuration runtime — base URL, timeouts, logs, feature flags (si besoin)
- [ ] **(Flutter · P0)** Client HTTP — interceptors auth, refresh token, retry, gestion 401/403/422/429/5xx
- [ ] **(Flutter · P0)** Gestion session — stockage sécurisé tokens + rotation/clear au logout
- [ ] **(Flutter · P1)** Modèles & sérialisation — DTO request/response pour tous les endpoints (génération si possible)
- [ ] **(Flutter · P1)** Gestion erreurs UI — mapping erreurs API → messages + états (vide/chargement/erreur)
- [ ] **(Flutter · P1)** Téléchargements fichiers — sauvegarde + partage OS (exports/PDF)
- [ ] **(Flutter · P1)** Internationalisation — FR (et EN si prévu) + formats dates/monnaie
- [ ] **(Flutter · P1)** Observabilité — logs structurés côté app + capture erreurs (crash reporting si prévu)

**Navigation & app shell**
- [ ] **(Flutter · P0)** Splash/Boot — init config + restore session + redirection
- [ ] **(Flutter · P0)** Auth guard — routes protégées selon session
- [ ] **(Flutter · P1)** Plan/bêta guard — UI conditionnelle selon `plan` / `beta_access`

**Auth & sécurité**
- [ ] **(Flutter · P0)** Inscription (`POST /api/v1/auth/register`) — formulaire + erreurs + création session
- [ ] **(Flutter · P0)** Connexion (`POST /api/v1/auth/login`) — formulaire + erreurs + session
- [ ] **(Flutter · P0)** Refresh (`POST /api/v1/auth/refresh`) — automatique via interceptor + retry requête
- [ ] **(Flutter · P0)** Déconnexion (`DELETE /api/v1/auth/logout`) — invalidate session + clear storage
- [ ] **(Flutter · P1)** Reset mot de passe — demander (`POST /api/v1/auth/password-reset/request`) + confirmer (`POST /api/v1/auth/password-reset/confirm`)
- [ ] **(Flutter · P2)** 2FA setup (`POST /api/v1/auth/2fa/setup`) — afficher secret + QR code (si fourni)
- [ ] **(Flutter · P2)** 2FA confirmer (`POST /api/v1/auth/2fa/confirm`) — écran code TOTP
- [ ] **(Flutter · P2)** 2FA vérifier login (`POST /api/v1/auth/2fa/verify`) — challenge code → tokens
- [ ] **(Flutter · P2)** 2FA désactiver (`DELETE /api/v1/auth/2fa`)

**Profil utilisateur & compte**
- [ ] **(Flutter · P0)** Profil courant (`GET /api/v1/users/me`) — écran compte + état plan/bêta
- [ ] **(Flutter · P1)** Mettre à jour profil (`PUT /api/v1/users/me`) — formulaire édition
- [ ] **(Flutter · P1)** Profil étendu (`PATCH /api/v1/users/me/extended-profile`) — préférences/infos additionnelles
- [ ] **(Flutter · P1)** Onboarding (`POST /api/v1/users/me/onboarding`) — flow initial (étapes + validation)
- [ ] **(Flutter · P1)** Female profile — lire (`GET /api/v1/users/me/female-profile`) + éditer (`PUT /api/v1/users/me/female-profile`)
- [ ] **(Flutter · P1)** Export données (`GET /api/v1/users/me/export`) — download + viewer/partage
- [ ] **(Flutter · P1)** Suppression compte (`DELETE /api/v1/users/me`) — confirmations + logout
- [ ] **(Flutter · P1)** Push token enregistrer (`POST /api/v1/users/me/device-token`) — FCM/APNs → send token
- [ ] **(Flutter · P1)** Push token retirer (`DELETE /api/v1/users/me/device-token`) — à logout / désactivation notif
- [ ] **(Flutter · P2)** Avatar upload (`POST /api/v1/users/me/avatar`) — caméra/galerie + upload multipart
- [ ] **(Flutter · P2)** Activation bêta (`POST /api/v1/users/me/beta-activate`) — écran code + feedback

**Dashboard**
- [ ] **(Flutter · P0)** Dashboard global (`GET /api/v1/dashboard`) — widgets : phase, résumé, raccourcis

**Cycle**
- [ ] **(Flutter · P0)** Créer un cycle (`POST /api/v1/cycle/records`) — formulaire (dates, flux, notes)
- [ ] **(Flutter · P0)** Liste cycles paginée (`GET /api/v1/cycle/records`) — pagination + filtres
- [ ] **(Flutter · P0)** Cycle courant (`GET /api/v1/cycle/current`) — phase + prédictions
- [ ] **(Flutter · P1)** Calendrier (`GET /api/v1/cycle/calendar`) — affichage calendrier + surlignage règles/ovulation
- [ ] **(Flutter · P1)** Symptômes cycle — ajouter (`POST /api/v1/cycle/symptoms`) + lister (`GET /api/v1/cycle/symptoms`)
- [ ] **(Flutter · P1)** Insights cycle (`GET /api/v1/cycle/insights`) — graphiques + recommandations
- [ ] **(Flutter · P1)** Export PDF cycle (`GET /api/v1/cycle/export/pdf`) — download + partage

**Mental**
- [ ] **(Flutter · P0)** Saisie humeur (`POST /api/v1/mental/mood`) — score + note
- [ ] **(Flutter · P0)** Historique humeurs (cursor) (`GET /api/v1/mental/moods`) — infinite scroll
- [ ] **(Flutter · P1)** Journal émotionnel — ajouter (`POST /api/v1/mental/journal`) + lister (`GET /api/v1/mental/journal`)
- [ ] **(Flutter · P1)** Prompt journal (`GET /api/v1/mental/journal/prompt`) — refresh + choix prompt
- [ ] **(Flutter · P1)** Techniques anti-stress (`GET /api/v1/mental/stress-techniques`) — catalogue + favoris (local)
- [ ] **(Flutter · P1)** Corrélations humeur (`GET /api/v1/mental/mood-correlation`) — graphiques
- [ ] **(Flutter · P1)** Détection SPM (`GET /api/v1/mental/spm-detection`) — résultat + explications
- [ ] **(Flutter · P1)** Insights mental (`GET /api/v1/mental/insights`) — synthèse + actions
- [ ] **(Flutter · P1)** Alertes — lister (`GET /api/v1/mental/alerts`) + résoudre (`PATCH /api/v1/mental/alerts/{alert_id}/resolve`)
- [ ] **(Flutter · P1)** Ressources (`GET /api/v1/mental/resources`) — liens + partage

**Rappels**
- [ ] **(Flutter · P1)** Lire rappels (`GET /api/v1/reminders`)
- [ ] **(Flutter · P1)** Mettre à jour un rappel (`PUT /api/v1/reminders/{reminder_type}`)
- [ ] **(Flutter · P1)** Supprimer un rappel (`DELETE /api/v1/reminders/{reminder_type}`)
- [ ] **(Flutter · P2)** Scheduling local — refléter les rappels (si l’app gère des notifs locales)

**Fertilité**
- [ ] **(Flutter · P1)** Logs fertilité — ajouter/maj (`POST /api/v1/fertility/logs`) + lister (`GET /api/v1/fertility/logs`)
- [ ] **(Flutter · P1)** Score fertilité (`GET /api/v1/fertility/score`) — affichage + explications
- [ ] **(Flutter · P1)** Essais conception — ajouter (`POST /api/v1/fertility/attempts`) + lister (`GET /api/v1/fertility/attempts`)
- [ ] **(Flutter · P2)** Coach fertilité (`POST /api/v1/fertility/coach`) — UI chat/résultats

**Grossesse & postpartum**
- [ ] **(Flutter · P1)** Activer grossesse (`POST /api/v1/pregnancy/activate`)
- [ ] **(Flutter · P1)** Lire profil grossesse (`GET /api/v1/pregnancy/profile`)
- [ ] **(Flutter · P1)** Passer postpartum (`POST /api/v1/pregnancy/postpartum`)
- [ ] **(Flutter · P1)** Contenu semaine (`GET /api/v1/pregnancy/week/{week}`) — page semaine + conseils
- [ ] **(Flutter · P1)** Symptômes grossesse — ajouter (`POST /api/v1/pregnancy/symptoms`) + lister (`GET /api/v1/pregnancy/symptoms`)
- [ ] **(Flutter · P1)** RDV grossesse — créer (`POST /api/v1/pregnancy/appointments`) + lister (`GET /api/v1/pregnancy/appointments`)
- [ ] **(Flutter · P1)** Allaitement — créer (`POST /api/v1/pregnancy/breastfeeding`) + lister (`GET /api/v1/pregnancy/breastfeeding`)
- [ ] **(Flutter · P2)** EPDS — soumettre (`POST /api/v1/pregnancy/epds`) + UI score/ressources

**Santé hormonale**
- [ ] **(Flutter · P1)** Douleurs — ajouter (`POST /api/v1/hormonal-health/pain`) + lister (`GET /api/v1/hormonal-health/pain`)
- [ ] **(Flutter · P1)** Export douleurs PDF (`GET /api/v1/hormonal-health/pain/export/pdf`) — download + partage
- [ ] **(Flutter · P1)** PCOS — assessment (`POST /api/v1/hormonal-health/pcos/assessment`)
- [ ] **(Flutter · P1)** Endométriose — ressources (`GET /api/v1/hormonal-health/endometriosis/resources`)
- [ ] **(Flutter · P1)** Traitements — créer (`POST /api/v1/hormonal-health/treatments`) + lister (`GET /api/v1/hormonal-health/treatments`)

**Ménopause**
- [ ] **(Flutter · P1)** Logs ménopause — créer (`POST /api/v1/menopause/logs`) + lister (`GET /api/v1/menopause/logs`)
- [ ] **(Flutter · P1)** Hot flash quick add (`POST /api/v1/menopause/hot-flash`)
- [ ] **(Flutter · P1)** Insights ménopause (`GET /api/v1/menopause/insights`)
- [ ] **(Flutter · P1)** Screening périménopause (`POST /api/v1/menopause/perimenopause/screening`)
- [ ] **(Flutter · P1)** Export PDF ménopause (`GET /api/v1/menopause/export/pdf`)

**Nutrition**
- [ ] **(Flutter · P1)** Logs nutrition — créer (`POST /api/v1/nutrition/logs`) + lister (`GET /api/v1/nutrition/logs`)
- [ ] **(Flutter · P1)** Plan nutrition (`GET /api/v1/nutrition/plan`)
- [ ] **(Flutter · P1)** Recettes recommandées (`GET /api/v1/nutrition/recipes`)
- [ ] **(Flutter · P1)** Suppléments recommandés (`GET /api/v1/nutrition/supplements`)
- [ ] **(Flutter · P1)** Liste de courses (`GET /api/v1/nutrition/shopping-list`) — export + checklist
- [ ] **(Flutter · P2)** Coach nutrition (`POST /api/v1/nutrition/coach`) — UI chat/résultats

**Santé intime**
- [ ] **(Flutter · P1)** Libido — ajouter (`POST /api/v1/intimate/libido`) + lister (`GET /api/v1/intimate/libido`)
- [ ] **(Flutter · P1)** Santé intime (log) — ajouter (`POST /api/v1/intimate/health-log`) + lister (`GET /api/v1/intimate/health-log`)
- [ ] **(Flutter · P1)** Guide contraception (`GET /api/v1/intimate/contraception-guide`)
- [ ] **(Flutter · P1)** Santé vaginale (`GET /api/v1/intimate/vaginal-health`)
- [ ] **(Flutter · P1)** Éducation sexuelle (`GET /api/v1/intimate/sexual-education`)
- [ ] **(Flutter · P2)** Conseil personnalisé (`POST /api/v1/intimate/advice`)

**Communauté**
- [ ] **(Flutter · P1)** Posts — créer (`POST /api/v1/community/posts`) + lister (`GET /api/v1/community/posts`)
- [ ] **(Flutter · P1)** Like post (`POST /api/v1/community/posts/{post_id}/like`)
- [ ] **(Flutter · P1)** Mes posts (`GET /api/v1/community/posts/mine`)
- [ ] **(Flutter · P1)** Recettes — créer (`POST /api/v1/community/recipes`) + lister (`GET /api/v1/community/recipes`)
- [ ] **(Flutter · P1)** Like recette (`POST /api/v1/community/recipes/{recipe_id}/like`)
- [ ] **(Flutter · P1)** Défis — lister (`GET /api/v1/community/challenges`)
- [ ] **(Flutter · P1)** Défis — s’inscrire (`POST /api/v1/community/challenges/{challenge_id}/enroll`)
- [ ] **(Flutter · P1)** Défis — progression (`PATCH /api/v1/community/challenges/{challenge_id}/progress`)
- [ ] **(Flutter · P1)** Mes défis (`GET /api/v1/community/challenges/mine`)

**Consultation**
- [ ] **(Flutter · P1)** Réserver (`POST /api/v1/consultation/book`)
- [ ] **(Flutter · P1)** Mes réservations (`GET /api/v1/consultation/bookings`)
- [ ] **(Flutter · P1)** Préparation consultation (`GET /api/v1/consultation/preparation`)
- [ ] **(Flutter · P2)** Rapport mensuel PDF (`POST /api/v1/consultation/monthly-report/pdf`) — génération + download
- [ ] **(Flutter · P1)** Infos support (`GET /api/v1/consultation/support-info`)

**Chat**
- [ ] **(Flutter · P1)** Envoyer message (`POST /api/v1/chat/message`) — UI conversation + streaming si ajouté plus tard
- [ ] **(Flutter · P1)** Sessions (`GET /api/v1/chat/sessions`) — liste des conversations
- [ ] **(Flutter · P1)** Messages session (`GET /api/v1/chat/sessions/{session_id}`) — timeline + pagination si ajoutée

**Paiements**
- [ ] **(Flutter · P1)** Checkout (`POST /api/v1/payments/checkout`) — ouvrir URL checkout (webview / navigateur)
- [ ] **(Flutter · P1)** Portail facturation (`POST /api/v1/payments/portal`) — ouvrir URL portail
- [ ] **(Flutter · P1)** Factures paginées (`GET /api/v1/payments/invoices`) — liste + download PDF si disponible

**Admin (optionnel : app interne)**
- [ ] **(Flutter · P2)** Admin — lister users (`GET /api/v1/admin/users`)
- [ ] **(Flutter · P2)** Admin — changer plan (`PATCH /api/v1/admin/users/{user_id}/plan`)
- [ ] **(Flutter · P2)** Admin — toggle bêta (`PATCH /api/v1/admin/users/{user_id}/beta`)
- [ ] **(Flutter · P2)** Admin — supprimer user (`DELETE /api/v1/admin/users/{user_id}`)

**Webhooks (non mobile)**
- [ ] **(Backend uniquement)** Stripe webhook (`POST /api/v1/payments/webhook`) — pas de tâche Flutter
- [ ] **(Backend uniquement)** Telegram webhook (`POST /api/v1/bot/telegram/webhook`) — pas de tâche Flutter

### Bloqué

- [ ] *(aucune pour le moment)*

### En cours

- [ ] *(aucune pour le moment)*

### Fait

- [ ] *(aucune pour le moment)*

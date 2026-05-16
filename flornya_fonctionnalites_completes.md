# FlorNya — Liste Complète des Fonctionnalités

> **"Fleuris à chaque étape."**
> 78 fonctionnalités · 3 phases · 6 mois · 8 modules · International

---

## Légende

| Badge | Plan | Prix |
|---|---|---|
| 🟢 **Gratuit** | Essentiel (limité) | 0$ |
| 🔵 **Essentiel** | Essentiel | 5$ / mois |
| 🟠 **Bloom** | Bloom | 12$ / mois |
| 🟣 **Bloom Pro** | Bloom Pro | 25$ / mois |

**Plateformes :** `WEB` · `PWA` = Mobile PWA · `TG` = Telegram · `WA` = WhatsApp

---

## Phase 1 — MVP · *Le cœur de l'app* · Mois 1–2

---

### 🔐 Authentification & Compte

| # | Fonctionnalité | Description | Plan | Plateformes |
|---|---|---|---|---|
| 1 | **Inscription par email** | Création de compte avec email + mot de passe. Vérification email obligatoire. Saisie de la date de naissance (obligatoire pour la vérification d'âge). | 🟢 Gratuit | WEB · TG · WA |
| 2 | **Connexion sécurisée** | Login JWT avec access token (15min) + refresh token (30j), rotation automatique. | 🟢 Gratuit | WEB · TG · WA |
| 3 | **Réinitialisation mot de passe** | Lien de réinitialisation envoyé par email, token valable 1 heure. | 🟢 Gratuit | WEB |
| 4 | **Onboarding féminin (6 étapes)** | Wizard personnalisé : prénom, âge, stade de vie (cycle, grossesse, ménopause…), durée moyenne du cycle, dernières règles, conditions de santé (SOPK, endométriose), cuisine préférée. | 🟢 Gratuit | WEB · TG |
| 5 | **Gestion du profil** | Modifier prénom, photo, langue (FR/EN), préférences, stade de vie, allergies. | 🟢 Gratuit | WEB |
| 6 | **Export données RGPD** | Export JSON/CSV complet de toutes les données personnelles déchiffrées. | 🟢 Gratuit | WEB |
| 7 | **Suppression de compte** | Suppression irréversible avec anonymisation sous 30j. | 🟢 Gratuit | WEB |
| 8 | **Double authentification (2FA)** | TOTP via Google Authenticator. Obligatoire pour Bloom Pro. | 🟢 Gratuit | WEB |
| 9 | **Protection des mineures** | Vérification d'âge dès l'inscription (minimum 13 ans). Contenu 18+ bloqué pour les moins de 18 ans. Ton IA adapté pour les adolescentes. | 🟢 Gratuit | WEB · PWA |

---

### 🔴 Module 1 — Suivi du Cycle Menstruel

| # | Fonctionnalité | Description | Plan | Plateformes |
|---|---|---|---|---|
| 10 | **Saisie des règles** | Enregistrement du début et de la fin des règles, durée, intensité du flux (léger / moyen / abondant / spotting). | 🔵 Essentiel | WEB · TG |
| 11 | **Prédiction du cycle** | Algorithme de prédiction des prochaines règles basé sur l'historique personnel. Précision affinée cycle après cycle. | 🔵 Essentiel | WEB · TG |
| 12 | **Phases du cycle** | Visualisation des 4 phases : menstruelle, folliculaire, ovulatoire, lutéale. Explication des effets de chaque phase sur le corps et l'humeur. | 🔵 Essentiel | WEB |
| 13 | **Phase actuelle en temps réel** | Indicateur animé de la phase actuelle (J+n du cycle) mis à jour chaque jour. | 🔵 Essentiel | WEB · PWA |
| 14 | **Prédiction ovulation** | Fenêtre fertile calculée et visualisée sur le calendrier. Notification J-2 avant l'ovulation. | 🔵 Essentiel | WEB · TG |
| 15 | **Calendrier du cycle** | Vue calendrier mensuelle colorée selon les phases. Navigation historique illimitée. | 🔵 Essentiel | WEB · PWA |
| 16 | **Journal des symptômes** | Suivi quotidien : crampes, ballonnements, seins sensibles, maux de tête, acné, fatigue, libido, énergie, qualité du sommeil. Intensité de 1 à 3. | 🔵 Essentiel | WEB · TG |
| 17 | **Rappel avant les règles** | Notification personnalisable J-2 ou J-3 avant le début prévu des règles. | 🔵 Essentiel | WEB · TG · WA |
| 18 | **Insights IA sur le cycle** | Analyse IA des patterns : régularité du cycle, symptômes récurrents, corrélations humeur / phase, tendances sur 3 mois. | 🟠 Bloom | WEB |
| 19 | **Export cycle pour médecin** | Export PDF du suivi cycle des 6 derniers mois pour consultation gynécologique. | 🟣 Bloom Pro | WEB |

---

### 💳 Paiements & Abonnements

| # | Fonctionnalité | Description | Plan | Plateformes |
|---|---|---|---|---|
| 20 | **Abonnement Essentiel** | Abonnement 5$/mois via Stripe. Cycle, rappels, journal de base. Résiliation en 1 clic. | 🔵 Essentiel | WEB |
| 21 | **Abonnement Bloom** | Abonnement 12$/mois. Tout Essentiel + Coach IA, nutrition, fertilité, santé mentale. | 🟠 Bloom | WEB |
| 22 | **Abonnement Bloom Pro** | Abonnement 25$/mois. Tout Bloom + Consultation gynéco vidéo + Rapport médical PDF + Support 24/7. | 🟣 Bloom Pro | WEB |
| 23 | **Historique de facturation** | Accès à toutes les factures téléchargeables en PDF. Portail Stripe Customer. | 🟢 Gratuit | WEB |

---

### 🔔 Rappels & Notifications

| # | Fonctionnalité | Description | Plan | Plateformes |
|---|---|---|---|---|
| 24 | **Rappels médicaments / contraception** | Rappels configurables pour la prise de pilule, changement de patch, renouvellement d'implant. Répétition quotidienne. | 🔵 Essentiel | WEB · TG · WA |
| 25 | **Rappels hydratation** | Rappels réguliers pour boire de l'eau, adaptés selon la phase du cycle. | 🔵 Essentiel | TG · WA |
| 26 | **Rappel check-in émotionnel** | Rappel quotidien (soir) pour saisir l'humeur du jour. Désactivable. | 🔵 Essentiel | WEB · TG · WA |

---

## Phase 2 — Enrichissement · *L'expérience complète* · Mois 3–4

---

### 🌱 Module 2 — Fertilité & Conception

| # | Fonctionnalité | Description | Plan | Plateformes |
|---|---|---|---|---|
| 27 | **Mode conception** | Activation d'un mode dédié avec conseils optimisés pour maximiser les chances de conception naturelle. | 🟠 Bloom | WEB · TG |
| 28 | **Score de fertilité journalier** | Indicateur circulaire du score de fertilité du jour (0–100%) basé sur la phase, la BBT et la glaire cervicale. | 🟠 Bloom | WEB · PWA |
| 29 | **Suivi température basale (BBT)** | Saisie de la température basale matinale. Courbe BBT pour confirmer l'ovulation. Valeur chiffrée en BDD. | 🟠 Bloom | WEB · PWA |
| 30 | **Suivi glaire cervicale** | Journal de la glaire cervicale (sèche / crémeuse / filante / aqueuse) pour affiner la prédiction fertile. | 🟠 Bloom | WEB |
| 31 | **Suivi tests d'ovulation (LH)** | Enregistrement des résultats des tests LH (négatif / positif / pic). Interprétation automatique. | 🟠 Bloom | WEB |
| 32 | **Coach fertilité IA** | Conseils personnalisés : alimentation pro-fertilité, style de vie, timing optimal, gestion du stress et fertilité. | 🟠 Bloom | WEB · TG |
| 33 | **Journal des tentatives** | Journal privé et chiffré des tentatives de conception. Corrélations avec le calendrier fertile. | 🟠 Bloom | WEB |
| 34 | **Ressources FIV / PMA** | Informations sur les traitements de fertilité (FIV, IUI, PMA) si les tentatives naturelles échouent après 12 mois. | 🟣 Bloom Pro | WEB |

---

### 🤱 Module 3 — Grossesse & Post-partum

| # | Fonctionnalité | Description | Plan | Plateformes |
|---|---|---|---|---|
| 35 | **Activation mode grossesse** | Détection automatique du retard + conseils immédiats post-test positif. Activation manuelle ou automatique. | 🟠 Bloom | WEB · TG |
| 36 | **Suivi semaine par semaine** | Développement du bébé semaine par semaine avec visuels comparatifs (taille d'un fruit…) et infos médicales clés. | 🟠 Bloom | WEB · PWA |
| 37 | **Journal des symptômes grossesse** | Suivi des nausées, fatigue, douleurs, mouvements fœtaux. L'IA distingue symptômes normaux vs signaux d'alarme. | 🟠 Bloom | WEB · TG |
| 38 | **Nutrition grossesse** | Plan nutritionnel adapté à chaque trimestre : acide folique, fer, calcium, oméga-3. Recettes adaptées. | 🟠 Bloom | WEB |
| 39 | **Calendrier des RDV médicaux** | Suivi des consultations prénatales, échographies, examens. Rappels automatiques J-7 et J-1. | 🟠 Bloom | WEB · TG |
| 40 | **Préparation accouchement** | Guides pratiques : valise de maternité, plan de naissance, techniques de respiration, signaux de travail. | 🟠 Bloom | WEB |
| 41 | **Mode post-partum** | Activation automatique après la DPA. Suivi de la récupération physique et émotionnelle de la mère. | 🟠 Bloom | WEB · TG |
| 42 | **Questionnaire EPDS (dépression post-partum)** | Questionnaire Edinburgh EPDS envoyé tous les 15 jours en post-partum. Score < 10 : encouragements. Score 10–12 : ressources bien-être. Score ≥ 13 : alerte professionnelle immédiate + numéros d'aide. Score chiffré en BDD. | 🟠 Bloom | WEB · TG |
| 43 | **Suivi allaitement** | Journal des tétées (durée, sein, quantité). Conseils IA sur l'allaitement et gestion des difficultés. | 🟠 Bloom | WEB · PWA |
| 44 | **Retour de couches** | Prédiction et suivi du retour des règles après l'accouchement. Reprise de la contraception. | 🟠 Bloom | WEB · TG |

---

### ⚡ Module 4 — Santé Hormonale (SOPK, Endométriose)

| # | Fonctionnalité | Description | Plan | Plateformes |
|---|---|---|---|---|
| 45 | **Score de risque SOPK** | Questionnaire IA pour évaluer le risque de SOPK. Liste de symptômes à surveiller et à présenter au médecin. | 🟠 Bloom | WEB |
| 46 | **Journal douleur endométriose** | Journal dédié à la douleur pelvienne, dysménorrhée, dyspareunie. Cartographie de la douleur par zone du corps. | 🟠 Bloom | WEB · PWA |
| 47 | **Conseils SOPK** | Nutrition anti-inflammatoire, gestion du poids, activité physique adaptée, suppléments recommandés. | 🟠 Bloom | WEB |
| 48 | **Suivi traitement hormonal** | Journal des traitements hormonaux (pilule, DIU, patch, implant). Effets ressentis. Rappels de prise. | 🔵 Essentiel | WEB · TG |
| 49 | **Rapport douleur pour médecin** | Export PDF du journal de douleur sur 3 mois pour consultation gynécologique ou spécialiste. | 🟣 Bloom Pro | WEB |
| 50 | **Ressources diagnostics** | Guides sur les examens diagnostiques (échographie, laparoscopie, bilan hormonal). Questions à poser au médecin. | 🟠 Bloom | WEB |

---

### 🍂 Module 5 — Ménopause & Périménopause

| # | Fonctionnalité | Description | Plan | Plateformes |
|---|---|---|---|---|
| 51 | **Détection périménopause** | Questionnaire IA pour détecter les signes précoces (cycles irréguliers, bouffées de chaleur, insomnie, sécheresse). | 🟠 Bloom | WEB |
| 52 | **Journal symptômes ménopause** | Suivi quotidien : bouffées de chaleur, sueurs nocturnes, sécheresse vaginale, insomnie, sautes d'humeur, prise de poids. | 🟠 Bloom | WEB · TG |
| 53 | **Gestion bouffées de chaleur** | Bouton d'enregistrement rapide. Techniques de gestion immédiate (respiration, vêtements, température ambiante). Suivi de la fréquence. | 🟠 Bloom | WEB · PWA |
| 54 | **Nutrition ménopause** | Plan nutritionnel dédié : calcium, vitamine D, phyto-estrogènes, aliments à éviter. Recettes adaptées. | 🟠 Bloom | WEB |
| 55 | **Santé osseuse** | Suivi du risque d'ostéoporose. Conseils exercice physique pour préserver la densité osseuse. | 🟠 Bloom | WEB |
| 56 | **THS informatif** | Informations équilibrées et sourcées sur le Traitement Hormonal de Substitution. Questions à poser au médecin. | 🟠 Bloom | WEB |
| 57 | **Rapport ménopause** | Export PDF complet du suivi ménopause pour consultation spécialisée. | 🟣 Bloom Pro | WEB |

---

### 🥗 Module 6 — Nutrition Féminine & Hormones

| # | Fonctionnalité | Description | Plan | Plateformes |
|---|---|---|---|---|
| 58 | **Plan nutritionnel par phase hormonale** | Plan alimentaire adapté à chaque phase du cycle : phase menstruelle (fer, anti-inflammatoires), folliculaire (légèreté), ovulatoire (antioxydants, zinc), lutéale (magnésium, fibres). | 🟠 Bloom | WEB · TG |
| 59 | **Recettes hormonales** | Bibliothèque de recettes anti-inflammatoires, pro-fertilité, anti-SPM. Filtrables par culture culinaire (africaine, asiatique, méditerranéenne…). | 🟠 Bloom | WEB |
| 60 | **Coach nutrition IA** | Réponses aux questions nutritionnelles liées aux hormones. Substitutions alimentaires. Conseils contextualisés selon la phase. | 🟠 Bloom | WEB · TG · WA |
| 61 | **Journal alimentaire** | Saisie des repas quotidiens avec analyse de l'impact hormonal estimé par l'IA. | 🟠 Bloom | WEB · TG |
| 62 | **Suppléments recommandés** | Informations sur les suppléments utiles (oméga-3, magnésium, vitamine D, fer, vitamine B6) selon la phase et le profil. | 🟠 Bloom | WEB |
| 63 | **Liste de courses hormonale** | Génération automatique d'une liste de courses alignée sur le plan nutritionnel de la semaine, organisée par rayon. | 🟠 Bloom | WEB · PWA |

---

## Phase 3 — Croissance · *L'écosystème FlorNya* · Mois 5–6

---

### 🧠 Module 7 — Santé Mentale liée aux Hormones

| # | Fonctionnalité | Description | Plan | Plateformes |
|---|---|---|---|---|
| 64 | **Check-in émotionnel quotidien** | Saisie rapide de l'humeur du jour (score 1–5) + émotions ressenties. Moins de 2 minutes. | 🔵 Essentiel | WEB · TG · WA |
| 65 | **Corrélation humeur / cycle** | Graphique de corrélation humeur–phase sur les 3 derniers mois. Aide à anticiper les périodes difficiles. | 🟠 Bloom | WEB |
| 66 | **Détection SPM / TDPM** | Identification automatique du Syndrome Prémenstruel et du Trouble Dysphorique Prémenstruel. Alerte si patterns préoccupants. | 🟠 Bloom | WEB |
| 67 | **Journal émotionnel privé** | Journal intime chiffré (AES-256). Prompts bienveillants générés par l'IA selon l'humeur déclarée. Jamais en cache. | 🟠 Bloom | WEB · PWA |
| 68 | **Techniques de gestion du stress** | Exercices de respiration guidée, méditation, cohérence cardiaque adaptés à la phase du cycle et à l'humeur. | 🟠 Bloom | WEB · PWA |
| 69 | **Insights émotionnels IA** | L'IA analyse les patterns émotionnels et propose des stratégies personnalisées pour mieux vivre les phases difficiles. | 🟠 Bloom | WEB |
| 70 | **Ressources santé mentale** | Liens vers des professionnels spécialisés en santé mentale féminine. Lignes d'écoute locales selon le pays. | 🟢 Gratuit | WEB |
| 71 | **Alerte détresse émotionnelle** | Si le journal détecte une détresse émotionnelle répétée (3 jours consécutifs score ≤ 2), proposition de ressources d'aide adaptées. | 🟠 Bloom | WEB · TG |

---

### 💜 Module 8 — Bien-être Intime & Sexualité

| # | Fonctionnalité | Description | Plan | Plateformes |
|---|---|---|---|---|
| 72 | **Suivi de la libido** | Journal de la libido corrélé à la phase du cycle. Informations sur les variations normales selon les hormones. Réservé 18+. | 🟠 Bloom | WEB |
| 73 | **Santé vaginale** | Informations sur les pertes normales vs anormales, infections courantes (mycoses, vaginose bactérienne), conseils d'hygiène intime. | 🟠 Bloom | WEB |
| 74 | **Guide contraception** | Comparatif détaillé des méthodes contraceptives (pilule, DIU, implant, préservatif, contraception naturelle). Aide au choix personnalisé. | 🔵 Essentiel | WEB |
| 75 | **Rappels contraception** | Rappels de prise de pilule, renouvellement d'implant, changement de patch. Configurables. | 🔵 Essentiel | WEB · TG · WA |
| 76 | **Éducation sexuelle** | Contenus pédagogiques sur la sexualité féminine, le plaisir, le consentement, l'anatomie. Adaptés à l'âge (contenu 18+ protégé). | 🟠 Bloom | WEB |
| 77 | **Sécheresse intime** | Conseils pour gérer la sécheresse vaginale (ménopause, allaitement, stress hormonal). Orientation vers un professionnel. | 🟠 Bloom | WEB |
| 78 | **Douleurs pendant les rapports** | Informations sur la dyspareunie. Conseils pratiques et orientation vers un gynécologue ou sexologue. | 🟠 Bloom | WEB |

---

### 👥 Communauté & Social

| # | Fonctionnalité | Description | Plan | Plateformes |
|---|---|---|---|---|
| 79 | **Forum communautaire** | Espace d'échange bienveillant entre femmes. Modéré par IA. Espaces par thématique (cycle, fertilité, ménopause…) et tranche d'âge. | 🟠 Bloom | WEB |
| 80 | **Partage de recettes** | Publier et découvrir des recettes hormonales partagées par la communauté. Score nutritionnel calculé automatiquement. Likes et sauvegarde. | 🟠 Bloom | WEB |
| 81 | **Défis & objectifs collectifs** | Défis hebdomadaires (ex : "7 jours de journaling", "cycle sans sucre ajouté"). Badges à débloquer, progression visible. | 🟠 Bloom | WEB |

---

### 🎥 Consultations avec Professionnelles

| # | Fonctionnalité | Description | Plan | Plateformes |
|---|---|---|---|---|
| 82 | **Consultation vidéo gynécologue** | Prise de RDV et consultation vidéo avec une gynécologue certifiée. FlorNya prépare automatiquement un résumé du profil patiente avant chaque séance. | 🟣 Bloom Pro | WEB |
| 83 | **Rapport médical PDF mensuel** | Rapport complet PDF généré chaque mois : cycle, humeur, nutrition, symptômes. Partageable avec le médecin traitant. | 🟣 Bloom Pro | WEB |
| 84 | **Préparation de consultation** | Résumé structuré généré par l'IA (cycle, douleurs, humeur, questions à poser) à envoyer à la gynécologue avant la séance. | 🟣 Bloom Pro | WEB |
| 85 | **Support prioritaire 24/7** | Accès à un support humain prioritaire. Réponse garantie sous 2 heures. | 🟣 Bloom Pro | WEB |

---

### ⚡ Fonctionnalités Transversales & Avancées

| # | Fonctionnalité | Description | Plan | Plateformes |
|---|---|---|---|---|
| 86 | **Chat coach IA FlorNya** | Conversation libre avec le coach IA sur tout sujet de santé féminine. Ton adapté selon l'âge et le stade de vie. Disclaimer médical automatique. | 🟠 Bloom | WEB · TG · WA |
| 87 | **Dashboard personnalisé** | Vue d'ensemble : phase actuelle, prochaines règles, humeur du jour, dernier rappel, objectif de la semaine. | 🔵 Essentiel | WEB · PWA |
| 88 | **Mode adolescente (13–17 ans)** | Interface et contenus pédagogiques adaptés. Ton simplifié. Contenu adulte entièrement bloqué. Encouragement à en parler à un adulte de confiance. | 🟢 Gratuit | WEB · PWA |
| 89 | **Internationalisation FR / EN** | Interface entièrement disponible en français et anglais. Détection automatique. Changement en 1 clic. Espagnol et portugais en Phase 3. | 🟢 Gratuit | WEB · PWA |
| 90 | **Dark mode** | Thème clair / sombre / automatique (selon système). Utile pour les consultations nocturnes. | 🟢 Gratuit | WEB · PWA |
| 91 | **PWA installable** | Installable sur smartphone sans App Store. Icône sur écran d'accueil. Expérience native. | 🟢 Gratuit | PWA |
| 92 | **Mode hors ligne (offline)** | Consultation du cycle, du plan nutritionnel et du journal en mode offline. Synchronisation au retour du réseau. | 🟢 Gratuit | PWA |
| 93 | **Notifications intelligentes** | Push personnalisées selon la phase du cycle, le profil et les préférences. Non intrusives, désactivables par type. | 🔵 Essentiel | WEB · PWA |
| 94 | **Accès anticipé aux nouveautés (bêta)** | Les abonnées Bloom et Bloom Pro testent les nouvelles fonctionnalités en avant-première. | 🟠 Bloom | WEB |

---

## Récapitulatif par plan

| Plan | Fonctionnalités clés incluses | Prix |
|---|---|---|
| 🟢 **Gratuit** | Inscription, connexion, onboarding, protection mineures, mode ado, dark mode, PWA, offline, i18n, export RGPD, ressources santé mentale, guide contraception (lecture), tableau de bord basique | 0$ |
| 🔵 **Essentiel** | Tout Gratuit + Cycle complet (saisie, prédiction, calendrier, phases, symptômes), rappels ×3, contraception (rappels + guide), check-in émotionnel, suivi traitement hormonal, dashboard, notifications, abonnement 5$/mois | 5$/mois |
| 🟠 **Bloom** | Tout Essentiel + Coach IA chat, fertilité ×8, grossesse & post-partum ×10 dont EPDS, santé hormonale ×4, ménopause ×6, nutrition ×6, santé mentale ×7, bien-être intime ×6, communauté ×3, insights IA cycle, corrélation humeur/cycle, plan nutritionnel par phase, forum, défis | 12$/mois |
| 🟣 **Bloom Pro** | Tout Bloom + Consultation vidéo gynécologue, rapport médical PDF mensuel, préparation consultation, support 24/7, export cycle PDF, rapport douleur PDF, rapport ménopause PDF, ressources FIV/PMA, 2FA obligatoire | 25$/mois |

---

## Récapitulatif par phase

| Phase | Période | Nouvelles fonctionnalités | Objectif |
|---|---|---|---|
| **Phase 1 — MVP** | Mois 1–2 | 26 fonctionnalités | 500 utilisatrices, valider le cycle de base |
| **Phase 2 — Enrichissement** | Mois 3–4 | 38 fonctionnalités | 2 000 utilisatrices, fertilité & grossesse |
| **Phase 3 — Croissance** | Mois 5–6 | 30 fonctionnalités | 10 000 utilisatrices, écosystème complet |
| **TOTAL** | 6 mois | **94 fonctionnalités** | |

---

## Récapitulatif par module

| Module | Fonctionnalités | Plan min. | Cible d'âge |
|---|---|---|---|
| 🔴 Cycle menstruel | 10 | Essentiel | 12–50 ans |
| 🌱 Fertilité & conception | 8 | Bloom | 18–45 ans |
| 🤱 Grossesse & post-partum | 10 | Bloom | 18–45 ans |
| ⚡ Santé hormonale | 6 | Bloom | 15–45 ans |
| 🍂 Ménopause & périménopause | 7 | Bloom | 40–60 ans |
| 🥗 Nutrition féminine | 6 | Bloom | Tous âges |
| 🧠 Santé mentale hormonale | 8 | Essentiel (base) | Tous âges |
| 💜 Bien-être intime | 7 | Essentiel (base) | 13+ / 18+ (intime) |
| 🔐 Auth & Compte | 9 | Gratuit | Tous âges |
| 💳 Paiements | 4 | Gratuit | Tous âges |
| 🔔 Rappels | 3 | Essentiel | Tous âges |
| 👥 Communauté | 3 | Bloom | Tous âges |
| 🎥 Consultations | 4 | Bloom Pro | Tous âges |
| ⚡ Transversales | 9 | Gratuit | Tous âges |

---

## Récapitulatif par plateforme

| Plateforme | Fonctionnalités disponibles |
|---|---|
| **Web** | Toutes les 94 fonctionnalités |
| **PWA Mobile** | Cycle, BBT, symptômes, humeur, grossesse semaine, bouffées de chaleur, liste courses, journal émotionnel, techniques stress, dashboard, offline, dark mode, i18n, notifications push |
| **Telegram** | Cycle (saisie + rappels), onboarding, chat IA, nutrition, check-in émotionnel, rappels ×4, rapport hebdo, grossesse (symptômes), ménopause (journal) |
| **WhatsApp** | Chat IA, rappels (médicaments, hydratation, check-in), notification rapport hebdo |

---

## Sécurité & Confidentialité — rappel

| Protection | Détail |
|---|---|
| **Données chiffrées AES-256** | Journal intime, notes cycle, BBT, score EPDS, notes consultations |
| **Vérification d'âge** | 13 ans minimum, contenu 18+ bloqué sous 18 ans |
| **EPDS ≥ 13** | Alerte professionnelle automatique + numéros d'aide |
| **Détresse émotionnelle** | Alerte si score ≤ 2 pendant 3 jours consécutifs |
| **RGPD** | Export + suppression + anonymisation sous 30j |
| **Zéro revente** | Données santé reproductives jamais partagées |
| **Mention légale** | Outil bien-être, pas dispositif médical certifié |

---

*Document généré le 13 Mai 2026 · FlorNya v1.0.0 · 94 fonctionnalités · Roadmap 6 mois*
*Stack : Python · FastAPI · React · PostgreSQL · Claude API · Stripe*

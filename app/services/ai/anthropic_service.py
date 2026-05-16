import anthropic

from app.config import get_settings

settings = get_settings()

_SYSTEM_BASE = (
    "Tu es Bloom, une assistante experte en santé féminine pour l'application FlorNya. "
    "Tes réponses sont bienveillantes, scientifiquement fondées et adaptées à l'utilisatrice. "
    "Ajoute toujours ce disclaimer : "
    "'Ces informations sont données à titre indicatif et ne remplacent pas un avis médical professionnel.' "
    "Ne dépasse jamais 500 mots. Utilise du Markdown structuré (## titres, listes)."
)


class AnthropicInsightService:
    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def _call(self, system: str, user_content: str, max_tokens: int = 700) -> str:
        message = self._client.messages.create(
            model=settings.AI_INSIGHTS_MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_content}],
        )
        return message.content[0].text  # type: ignore[index]

    # ── Cycle insights ────────────────────────────────────────────────────

    async def generate_cycle_insights(self, context: dict) -> str:
        cycle_count = context.get("cycle_count", 0)
        avg_length = context.get("avg_cycle_length")
        regularity = context.get("regularity_score")
        symptoms = context.get("dominant_symptoms", [])
        language = context.get("language", "fr")

        lang = "Réponds en français." if language == "fr" else f"Answer in {language}."

        content = f"""{lang}

Données du cycle de l'utilisatrice :
- Cycles enregistrés : {cycle_count}
- Longueur moyenne : {f"{avg_length:.1f} jours" if avg_length else "inconnue"}
- Score régularité : {f"{regularity:.0%}" if regularity is not None else "< 3 cycles"}
- Symptômes dominants (90j) : {", ".join(symptoms) if symptoms else "aucun"}

Génère une analyse cycle avec : 1) résumé régularité 2) conseils selon symptômes 3) recommandations lifestyle 4) disclaimer."""

        return self._call(_SYSTEM_BASE, content)

    # ── Fertility AI coach ────────────────────────────────────────────────

    async def fertility_coach(self, question: str, context: dict) -> str:
        lang = context.get("language", "fr")
        lang_inst = "Réponds en français." if lang == "fr" else f"Answer in {lang}."
        phase = context.get("cycle_phase", "inconnue")
        score = context.get("fertility_score")

        system = _SYSTEM_BASE + (
            " Tu es spécialisée en fertilité naturelle et conception. "
            "Tu guides les femmes qui essaient de concevoir."
        )

        content = f"""{lang_inst}
Phase actuelle du cycle : {phase}
Score de fertilité du jour : {f"{score:.0f}%" if score else "inconnu"}

Question de l'utilisatrice : {question}"""

        return self._call(system, content)

    # ── Pregnancy AI ──────────────────────────────────────────────────────

    async def pregnancy_symptom_analysis(self, symptoms: dict, week: int | None, language: str = "fr") -> str:
        lang = "Réponds en français." if language == "fr" else f"Answer in {language}."

        alarm_indicators = ["severe_headache", "vision_changes", "sudden_swelling", "heavy_bleeding"]
        has_alarm = any(symptoms.get(k, False) for k in alarm_indicators)

        system = _SYSTEM_BASE + (
            " Tu es experte en suivi de grossesse. Si tu détectes des signes d'alarme, "
            "indique clairement de consulter un médecin immédiatement."
        )

        content = f"""{lang}
Semaine de grossesse : SA {week if week else "inconnue"}
Symptômes déclarés : {symptoms}
Signes d'alarme détectés : {"OUI" if has_alarm else "non"}

Analyse ces symptômes et indique s'ils sont normaux pour cette semaine de grossesse.
{"⚠️ ATTENTION : certains signes nécessitent une consultation urgente." if has_alarm else ""}"""

        return self._call(system, content, max_tokens=500)

    async def generate_postpartum_message(self, epds_score: int, language: str = "fr") -> str:
        lang = "Réponds en français." if language == "fr" else f"Answer in {language}."

        if epds_score >= 13:
            tone = "alerte professionnelle bienveillante, urge à consulter un médecin ou appeler le 3114"
        elif epds_score >= 10:
            tone = "encouragement et ressources de soutien"
        else:
            tone = "félicitations chaleureuses et encouragements"

        content = f"""{lang}
Score EPDS de l'utilisatrice : {epds_score}/30
Ton à adopter : {tone}

Génère un message d'accompagnement adapté au score. Court (3-5 phrases max)."""

        return self._call(_SYSTEM_BASE, content, max_tokens=300)

    # ── Hormonal health AI ────────────────────────────────────────────────

    async def pcos_advice(self, symptoms: list[str], language: str = "fr") -> str:
        lang = "Réponds en français." if language == "fr" else f"Answer in {language}."
        system = _SYSTEM_BASE + " Tu es spécialisée en SOPK (Syndrome des Ovaires Polykystiques)."

        content = f"""{lang}
Symptômes SOPK identifiés : {", ".join(symptoms) if symptoms else "aucun spécifié"}

Génère des conseils pratiques : alimentation anti-inflammatoire, activité physique adaptée,
gestion du stress, suppléments recommandés pour le SOPK."""

        return self._call(system, content)

    # ── Menopause AI ──────────────────────────────────────────────────────

    async def generate_menopause_insights(self, context: dict) -> str:
        lang = context.get("language", "fr")
        lang_inst = "Réponds en français." if lang == "fr" else f"Answer in {lang}."
        avg_hf = context.get("avg_hot_flash_per_day")
        symptoms = context.get("most_common_symptoms", [])

        system = _SYSTEM_BASE + " Tu es experte en ménopause et périménopause."

        content = f"""{lang_inst}
Données de la dernière période :
- Bouffées de chaleur moyennes/jour : {f"{avg_hf:.1f}" if avg_hf else "non renseigné"}
- Symptômes les plus fréquents : {", ".join(symptoms) if symptoms else "aucun"}

Génère une analyse de la ménopause avec conseils lifestyle, nutrition, gestion des bouffées
de chaleur, santé osseuse et indication d'un suivi médical si nécessaire."""

        return self._call(system, content)

    async def perimenopause_assessment(self, signs: list[str], age: int, language: str = "fr") -> str:
        lang = "Réponds en français." if language == "fr" else f"Answer in {language}."
        system = _SYSTEM_BASE + " Tu es spécialisée en périménopause et transitions hormonales."

        content = f"""{lang}
Âge de l'utilisatrice : {age} ans
Signes déclarés : {", ".join(signs) if signs else "aucun"}

Évalue le risque de périménopause et génère des recommandations adaptées."""

        return self._call(system, content, max_tokens=500)

    # ── Nutrition AI ──────────────────────────────────────────────────────

    async def nutrition_coach(self, question: str, context: dict) -> str:
        lang = context.get("language", "fr")
        lang_inst = "Réponds en français." if lang == "fr" else f"Answer in {lang}."
        phase = context.get("cycle_phase", "inconnue")
        cuisine = context.get("cuisine_preference")
        stage = context.get("reproductive_stage", "menstruating")

        system = _SYSTEM_BASE + (
            " Tu es nutritionniste spécialisée en santé hormonale féminine. "
            "Tes conseils sont contextualisés selon la phase du cycle et le stade de vie."
        )

        content = f"""{lang_inst}
Phase du cycle : {phase}
Stade de vie : {stage}
Préférence culinaire : {cuisine or "non spécifiée"}

Question nutritionnelle : {question}"""

        return self._call(system, content)

    async def generate_nutritional_plan(self, context: dict) -> str:
        lang = context.get("language", "fr")
        lang_inst = "Réponds en français." if lang == "fr" else f"Answer in {lang}."
        phase = context.get("phase", "follicular")
        stage = context.get("reproductive_stage", "menstruating")
        cuisine = context.get("cuisine_preference")

        system = _SYSTEM_BASE + " Tu es experte en nutrition hormonale et phytothérapie."

        content = f"""{lang_inst}
Phase du cycle : {phase}
Stade de vie : {stage}
Préférence culinaire : {cuisine or "générale"}

Génère un plan nutritionnel détaillé pour cette phase avec :
- Nutriments clés à privilégier
- Aliments recommandés (liste)
- Aliments à limiter
- Exemple de journée alimentaire type
- Suppléments utiles pour cette phase"""

        return self._call(system, content, max_tokens=800)

    async def analyze_food_log(self, meals: list[str], phase: str, language: str = "fr") -> tuple[str, int]:
        lang = "Réponds en français." if language == "fr" else f"Answer in {language}."

        content = f"""{lang}
Phase du cycle actuelle : {phase}
Repas de la journée : {", ".join(meals)}

1. Analyse l'impact hormonal estimé (score 1-10 où 10 = excellent pour les hormones)
2. Points forts de cette alimentation
3. Suggestions d'amélioration adaptées à la phase {phase}

Format: commence par "SCORE: X/10" puis l'analyse."""

        response = self._call(_SYSTEM_BASE, content, max_tokens=500)

        score = 5
        for line in response.split("\n"):
            if line.startswith("SCORE:"):
                try:
                    score = int(line.split(":")[1].split("/")[0].strip())
                    score = max(1, min(10, score))
                except (ValueError, IndexError):
                    pass
                break

        return response, score

    # ── Mental health AI ──────────────────────────────────────────────────

    async def generate_emotional_insights(self, context: dict) -> str:
        lang = context.get("language", "fr")
        lang_inst = "Réponds en français." if lang == "fr" else f"Answer in {lang}."
        avg_score = context.get("average_mood_score")
        distress_days = context.get("distress_days", 0)
        dominant_emotions = context.get("dominant_emotions", [])
        cycle_phase = context.get("cycle_phase", "inconnue")

        system = _SYSTEM_BASE + (
            " Tu es experte en santé mentale féminine et neuro-endocrinologie. "
            "Aide à comprendre les liens entre hormones et émotions avec bienveillance."
        )

        content = f"""{lang_inst}
Phase actuelle : {cycle_phase}
Score d'humeur moyen (30j) : {f"{avg_score:.1f}/5" if avg_score else "non disponible"}
Jours de détresse détectés (score ≤ 2) : {distress_days}
Émotions dominantes : {", ".join(dominant_emotions) if dominant_emotions else "non précisées"}

Génère une analyse émotionnelle bienveillante avec :
1) Corrélation probable hormones/émotions
2) Points forts de gestion émotionnelle
3) Techniques personnalisées pour cette phase
4) Quand consulter un professionnel"""

        return self._call(system, content, max_tokens=700)

    async def generate_journal_prompt(self, mood_score: int, cycle_phase: str, language: str = "fr") -> str:
        lang = "Réponds en français." if language == "fr" else f"Answer in {language}."

        tone = "doux et réconfortant" if mood_score <= 2 else ("neutre et curieux" if mood_score <= 3 else "joyeux et énergisant")

        content = f"""{lang}
Score d'humeur du jour : {mood_score}/5
Phase du cycle : {cycle_phase}
Ton souhaité : {tone}

Génère un seul prompt de journaling bienveillant et personnel (2-3 phrases max).
Commence directement par la question ou l'invitation, sans introduction."""

        return self._call(_SYSTEM_BASE, content, max_tokens=150)

    async def detect_spm_pattern(self, mood_data: list[dict], symptom_data: list[dict], language: str = "fr") -> str:
        lang = "Réponds en français." if language == "fr" else f"Answer in {language}."

        system = _SYSTEM_BASE + (
            " Tu es experte en SPM (Syndrome PréMenstruel) et TDPM (Trouble Dysphorique PréMenstruel). "
            "Analyse les patterns comportementaux avec précision clinique."
        )

        content = f"""{lang}
Données d'humeur des 60 derniers jours : {mood_data[:10]}
Données de symptômes associées : {symptom_data[:10]}

Analyse les patterns pour détecter un SPM ou TDPM potentiel.
Format de réponse : SÉVÉRITÉ: [légère|modérée|sévère|non détecté]
Puis explication clinique et recommandations."""

        return self._call(system, content, max_tokens=500)

    # ── Intimate health AI ────────────────────────────────────────────────

    async def intimate_health_advice(self, concern: str, context: dict) -> str:
        lang = context.get("language", "fr")
        lang_inst = "Réponds en français." if lang == "fr" else f"Answer in {lang}."
        is_adult = context.get("is_adult", True)

        if not is_adult:
            return "Ce contenu est réservé aux utilisatrices de 18 ans et plus."

        system = _SYSTEM_BASE + (
            " Tu es gynécologue experte. Fournis des informations médicalement précises "
            "sur la santé intime féminine avec empathie. Toujours orienter vers un professionnel "
            "si nécessaire."
        )

        content = f"""{lang_inst}
Préoccupation de santé intime : {concern}
Phase du cycle : {context.get("cycle_phase", "inconnue")}
Stade de vie : {context.get("reproductive_stage", "menstruating")}

Réponds avec des informations médicales fiables, des conseils pratiques et l'orientation
vers un professionnel gynécologue si le cas le nécessite."""

        return self._call(system, content)

    # ── Community AI ──────────────────────────────────────────────────────

    async def moderate_community_post(self, title: str, body: str, language: str = "fr") -> dict:
        lang = "Réponds en français." if language == "fr" else f"Answer in {language}."

        content = f"""{lang}
Titre du post communautaire : {title[:200]}
Contenu : {body[:500]}

Modère ce post. Il doit être :
- Bienveillant et respectueux
- Sans contenu médical dangereux ou trompeur
- Sans harcèlement ou discrimination
- Sans données personnelles identifiables

Format : APPROUVÉ ou REFUSÉ, suivi de la raison en 1 phrase."""

        response = self._call(_SYSTEM_BASE, content, max_tokens=150)
        approved = "APPROUVÉ" in response.upper() or "APPROVED" in response.upper()
        return {"approved": approved, "reason": response}

    async def score_community_recipe(self, title: str, ingredients: list[str], phase: str | None, language: str = "fr") -> int:
        lang = "Réponds en français." if language == "fr" else f"Answer in {language}."

        content = f"""{lang}
Recette : {title}
Ingrédients : {", ".join(ingredients[:20])}
Phase du cycle ciblée : {phase or "générale"}

Note le score hormonal de cette recette de 1 à 10 (10 = excellent pour les hormones féminines).
Réponds uniquement par un chiffre entre 1 et 10."""

        response = self._call(_SYSTEM_BASE, content, max_tokens=10)
        try:
            score = int("".join(filter(str.isdigit, response[:5])))
            return max(1, min(10, score))
        except (ValueError, TypeError):
            return 5

    # ── Consultation AI ───────────────────────────────────────────────────

    async def generate_consultation_prep(self, context: dict) -> str:
        lang = context.get("language", "fr")
        lang_inst = "Réponds en français." if lang == "fr" else f"Answer in {lang}."

        system = _SYSTEM_BASE + (
            " Tu prépares le dossier patient pour une consultation gynécologique. "
            "Ton rôle est de structurer les informations de façon médicalement utile."
        )

        content = f"""{lang_inst}
Résumé du cycle récent : {context.get("cycle_summary", "non disponible")}
Symptômes récents : {context.get("recent_symptoms", [])}
Humeur moyenne (30j) : {context.get("avg_mood", "non renseigné")}
Médicaments/traitements : {context.get("treatments", [])}
Préoccupations notées : {context.get("concerns", [])}

Génère une préparation de consultation structurée :
## Résumé du cycle
## Symptômes à signaler
## Questions à poser au médecin
## Points d'attention prioritaires"""

        return self._call(system, content, max_tokens=800)

    async def generate_monthly_report_insights(self, context: dict) -> str:
        lang = context.get("language", "fr")
        lang_inst = "Réponds en français." if lang == "fr" else f"Answer in {lang}."

        content = f"""{lang_inst}
Mois : {context.get("month_name", "ce mois")}
Cycles enregistrés : {context.get("cycle_count", 0)}
Humeur moyenne : {context.get("avg_mood", "N/A")}
Symptômes principaux : {context.get("top_symptoms", [])}
Nutrition score moyen : {context.get("avg_nutrition_score", "N/A")}
Score de fertilité moyen : {context.get("avg_fertility_score", "N/A")}

Génère un résumé mensuel de santé avec 3 points forts et 2 axes d'amélioration."""

        return self._call(_SYSTEM_BASE, content, max_tokens=500)

    # ── Chat coach ────────────────────────────────────────────────────────

    async def chat_response(self, message: str, history: list[dict], context: dict) -> str:
        lang = context.get("language", "fr")
        lang_inst = "Réponds en français." if lang == "fr" else f"Answer in {lang}."
        first_name = context.get("first_name", "")
        cycle_phase = context.get("cycle_phase", "inconnue")
        reproductive_stage = context.get("reproductive_stage", "menstruating")
        age = context.get("age")

        system = (
            f"Tu es Bloom, le coach santé féminine de FlorNya. "
            f"{'Parle à ' + first_name + ' directement.' if first_name else ''} "
            f"Tu connais son profil : phase du cycle {cycle_phase}, stade {reproductive_stage}"
            f"{', ' + str(age) + ' ans' if age else ''}. "
            "Réponds de façon conversationnelle, bienveillante et personnalisée. "
            "Pour les urgences médicales, oriente immédiatement vers un professionnel. "
            "Disclaimer automatique si conseil médical. Réponds en moins de 300 mots. "
            f"{lang_inst}"
        )

        messages = []
        for h in history[-6:]:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": message})

        result = self._client.messages.create(
            model=settings.AI_INSIGHTS_MODEL,
            max_tokens=400,
            system=system,
            messages=messages,
        )
        return result.content[0].text  # type: ignore[index]

    async def generate_shopping_list(self, phase: str, cuisine: str | None, language: str = "fr") -> dict[str, list[str]]:
        lang = "Réponds en français." if language == "fr" else f"Answer in {language}."

        content = f"""{lang}
Phase du cycle : {phase}
Style culinaire : {cuisine or "méditerranéen"}

Génère une liste de courses pour cette semaine adaptée à la phase {phase}.
Format JSON strict : {{"légumes": [...], "fruits": [...], "protéines": [...], "céréales": [...], "herbes_épices": [...], "suppléments": [...]}}"""

        response = self._call(_SYSTEM_BASE, content, max_tokens=400)

        import json
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])
        except (json.JSONDecodeError, ValueError):
            pass

        return {
            "légumes": ["épinards", "brocoli", "carottes"],
            "fruits": ["baies", "avocat"],
            "protéines": ["lentilles", "saumon", "oeufs"],
            "céréales": ["quinoa", "avoine"],
            "herbes_épices": ["curcuma", "gingembre"],
            "suppléments": [],
        }

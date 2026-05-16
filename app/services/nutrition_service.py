import json
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_sensitive, encrypt_sensitive
from app.models.nutrition_log import NutritionLog
from app.models.user import User
from app.repositories.nutrition_repository import NutritionRepository
from app.schemas.cycle import CyclePhase
from app.schemas.nutrition import (
    NutritionCoachResponse,
    NutritionLogCreate,
    NutritionLogPublic,
    NutritionalPlanResponse,
    RecipePublic,
    ShoppingListResponse,
    SupplementRecommendation,
)

_PHASE_PLANS: dict[str, dict] = {
    CyclePhase.menstrual: {
        "description": "Récupération et renouvellement. Le fer et les anti-inflammatoires sont essentiels.",
        "key_nutrients": ["Fer", "Vitamine C", "Oméga-3", "Magnésium", "Vitamine B12"],
        "recommended": ["Lentilles", "Épinards", "Saumon", "Noix", "Chocolat noir", "Thé d'ortie", "Gingembre"],
        "to_limit": ["Alcool", "Caféine", "Sel en excès", "Sucre raffiné", "Produits laitiers (si crampes)"],
        "sample_meal": "Matin: porridge avoine + graines de chia + baies. Midi: salade épinards + lentilles + saumon + jus citron. Soir: bouillon légumes + quinoa + tofu.",
        "supplements": ["Magnésium bisglycinate 300mg", "Oméga-3 1000mg", "Fer (si carence confirmée)"],
    },
    CyclePhase.follicular: {
        "description": "Énergie croissante. Construisez et régénérez avec des aliments frais et légers.",
        "key_nutrients": ["Protéines légères", "Antioxydants", "Zinc", "Vitamine E", "Probiotiques"],
        "recommended": ["Pousses de légumes", "Œufs", "Yaourt", "Avocat", "Graines de tournesol", "Légumes colorés"],
        "to_limit": ["Plats lourds et gras", "Excès de viande rouge", "Aliments ultra-transformés"],
        "sample_meal": "Matin: smoothie épinards + banane + protéine végétale. Midi: bowl quinoa + légumes grillés + œuf mollet. Soir: légumes sautés + tofu + riz brun.",
        "supplements": ["Probiotiques", "Zinc 15mg", "Vitamine E 200 UI"],
    },
    CyclePhase.ovulatory: {
        "description": "Phase de pic hormonal. Antioxydants et fibres pour soutenir l'ovulation.",
        "key_nutrients": ["Zinc", "Vitamine B6", "Antioxydants", "Fibres solubles", "Lycopène"],
        "recommended": ["Tomates", "Carottes", "Graines de lin", "Brocoli", "Fruits rouges", "Noix du Brésil"],
        "to_limit": ["Alcool", "Caféine excessive", "Aliments pro-inflammatoires", "Soja en excès"],
        "sample_meal": "Matin: granola maison + fruits + yaourt. Midi: salade tomates + mozzarella + graines lin. Soir: wok légumes + saumon + riz basmati.",
        "supplements": ["Vitamine B6 50mg", "Acide folique 400mcg", "Coenzyme Q10"],
    },
    CyclePhase.luteal: {
        "description": "Précédant les règles. Magnésium et fibres pour réduire le SPM.",
        "key_nutrients": ["Magnésium", "Calcium", "Vitamine B6", "Fibres", "Vitamine D"],
        "recommended": ["Chocolat noir ≥70%", "Amandes", "Légumineuses", "Patate douce", "Huile d'olive", "Persil"],
        "to_limit": ["Sel", "Sucre raffiné", "Alcool", "Caféine (aggrave crampes)", "Laitages (si SPM)"],
        "sample_meal": "Matin: pain complet + beurre d'amande + banane. Midi: soupe lentilles + pain de seigle. Soir: poulet four + patate douce + brocoli vapeur.",
        "supplements": ["Magnésium 400mg", "Calcium 500mg", "Vitamine B6 100mg", "Vitamine D3 2000 UI"],
    },
}

_SUPPLEMENTS: list[dict] = [
    {"name": "Oméga-3 (EPA/DHA)", "benefit": "Anti-inflammatoire, santé cardio et hormonale", "dosage": "1000–2000mg/jour", "phases": ["menstrual", "follicular"], "caution": "Éviter à forte dose si anticoagulants"},
    {"name": "Magnésium bisglycinate", "benefit": "Réduit crampes SPM, anxiété, insomnie", "dosage": "300–400mg/soir", "phases": ["luteal", "menstrual"], "caution": "Peut causer diarrhée à forte dose"},
    {"name": "Vitamine D3", "benefit": "Santé osseuse, immunité, humeur", "dosage": "2000 UI/jour", "phases": ["luteal", "menstrual", "follicular", "ovulatory"], "caution": "Mesurer le taux sanguin avant supplémentation"},
    {"name": "Vitamine B6", "benefit": "Réduit SPM, soutient production de progestérone", "dosage": "50–100mg/jour (phase lutéale)", "phases": ["luteal", "ovulatory"], "caution": "Neuropathie à très haute dose (>200mg/j)"},
    {"name": "Zinc", "benefit": "Santé ovocytaire, peau, immunité", "dosage": "15–25mg/jour", "phases": ["follicular", "ovulatory"], "caution": "Prendre pendant le repas pour éviter les nausées"},
    {"name": "Inositol (Myo-inositol)", "benefit": "Régularise le cycle, améliore sensibilité insuline (SOPK)", "dosage": "2–4g/jour", "phases": ["menstrual", "follicular"], "caution": "Consulter si SOPK diagnostiqué"},
]


class NutritionService:
    def __init__(
        self,
        session: AsyncSession,
        nutrition_repo: NutritionRepository,
        ai_service: object | None = None,
    ):
        self.session = session
        self.nutrition_repo = nutrition_repo
        self.ai_service = ai_service

    # ── Food journal ──────────────────────────────────────────────────────

    async def log_meals(
        self, user: User, data: NutritionLogCreate, current_phase: CyclePhase | None = None
    ) -> NutritionLogPublic:
        meals_json = json.dumps(data.meals, ensure_ascii=False)
        ai_analysis = None
        impact_score = None

        if self.ai_service is not None and data.meals and current_phase:
            try:
                analysis_text, score = await self.ai_service.analyze_food_log(
                    data.meals, current_phase.value, user.language
                )
                ai_analysis = analysis_text
                impact_score = score
            except Exception:
                pass

        entity = await self.nutrition_repo.upsert(
            user_id=user.id,
            log_date=data.log_date,
            meals_encrypted=encrypt_sensitive(meals_json),
            hormonal_impact_score=impact_score,
            ai_analysis_encrypted=encrypt_sensitive(ai_analysis),
            water_glasses=data.water_glasses,
            notes_encrypted=encrypt_sensitive(data.notes),
        )
        await self.session.commit()
        await self.session.refresh(entity)
        return self._to_public(entity)

    async def list_logs(
        self, user: User, date_from: date | None = None, date_to: date | None = None
    ) -> list[NutritionLogPublic]:
        items = await self.nutrition_repo.list_range(
            user_id=user.id, date_from=date_from, date_to=date_to
        )
        return [self._to_public(e) for e in items]

    # ── Nutritional plan ──────────────────────────────────────────────────

    async def get_nutritional_plan(
        self, user: User, phase: CyclePhase, reproductive_stage: str | None = None
    ) -> NutritionalPlanResponse:
        plan_data = _PHASE_PLANS.get(phase, _PHASE_PLANS[CyclePhase.follicular])

        sample_meal = plan_data["sample_meal"]

        if self.ai_service is not None:
            try:
                context = {
                    "phase": phase.value,
                    "reproductive_stage": reproductive_stage or "menstruating",
                    "cuisine_preference": None,
                    "language": user.language,
                }
                ai_plan = await self.ai_service.generate_nutritional_plan(context)
                sample_meal = ai_plan
            except Exception:
                pass

        return NutritionalPlanResponse(
            phase=phase.value,
            phase_description=plan_data["description"],
            key_nutrients=plan_data["key_nutrients"],
            recommended_foods=plan_data["recommended"],
            foods_to_limit=plan_data["to_limit"],
            sample_meal_plan=sample_meal,
            supplements=plan_data["supplements"],
        )

    # ── Recipes ───────────────────────────────────────────────────────────

    def get_recipes(self, phase: CyclePhase | None = None) -> list[RecipePublic]:
        all_recipes = [
            RecipePublic(
                title="Porridge anti-SPM au chocolat noir",
                phase="luteal",
                prep_time_minutes=10,
                ingredients=["80g flocons d'avoine", "200ml lait végétal", "2 carrés chocolat noir ≥70%", "1 banane", "1 c.à.s graines de chia", "Cannelle"],
                instructions="Cuire les flocons dans le lait 5 min. Ajouter chocolat fondu, banane tranchée, chia et cannelle.",
                nutritional_benefits="Magnésium (crampes), tryptophane (humeur), fibres (équilibre glycémique)",
                cultural_style="universel",
            ),
            RecipePublic(
                title="Bowl fertilité : quinoa, saumon, avocat",
                phase="ovulatory",
                prep_time_minutes=20,
                ingredients=["150g quinoa cuit", "100g saumon fumé", "½ avocat", "Concombre", "Graines de lin", "Citron", "Aneth"],
                instructions="Disposer le quinoa en base. Ajouter saumon, avocat tranché, concombre. Saupoudrer de graines de lin. Arroser de citron.",
                nutritional_benefits="Oméga-3 (fertilité), zinc (qualité ovocytaire), vitamine E",
                cultural_style="méditerranéen",
            ),
            RecipePublic(
                title="Soupe de lentilles corail au gingembre",
                phase="menstrual",
                prep_time_minutes=30,
                ingredients=["200g lentilles corail", "1 oignon", "2 carottes", "1 cm gingembre frais", "Curcuma", "Bouillon légumes 1L", "Jus de citron"],
                instructions="Faire revenir oignon, ajouter lentilles, carottes, gingembre, curcuma. Couvrir de bouillon. Cuire 20 min. Mixer. Finir avec jus de citron.",
                nutritional_benefits="Fer (pertes menstruelles), anti-inflammatoire (gingembre/curcuma), protéines végétales",
                cultural_style="africain/asiatique",
            ),
            RecipePublic(
                title="Smoothie détox phase folliculaire",
                phase="follicular",
                prep_time_minutes=5,
                ingredients=["Poignée épinards", "1 banane congelée", "1 kiwi", "Jus ½ citron", "200ml eau de coco", "Graines de chanvre"],
                instructions="Blender tous les ingrédients jusqu'à consistance lisse.",
                nutritional_benefits="Antioxydants (kiwi), fer végétal (épinards), énergie naturelle (eau de coco)",
                cultural_style="universel",
            ),
        ]

        if phase is not None:
            return [r for r in all_recipes if r.phase == phase.value]
        return all_recipes

    # ── Supplements ───────────────────────────────────────────────────────

    def get_supplements(self, phase: CyclePhase | None = None) -> list[SupplementRecommendation]:
        recommendations = [
            SupplementRecommendation(
                name=s["name"],
                benefit=s["benefit"],
                dosage_suggestion=s["dosage"],
                phases_recommended=s["phases"],
                caution=s.get("caution"),
            )
            for s in _SUPPLEMENTS
        ]
        if phase is not None:
            return [r for r in recommendations if phase.value in r.phases_recommended]
        return recommendations

    # ── Shopping list ─────────────────────────────────────────────────────

    async def get_shopping_list(
        self, user: User, phase: CyclePhase, cuisine_preference: str | None = None
    ) -> ShoppingListResponse:
        items_by_category: dict[str, list[str]] = {}

        if self.ai_service is not None:
            try:
                items_by_category = await self.ai_service.generate_shopping_list(
                    phase.value, cuisine_preference, user.language
                )
            except Exception:
                pass

        if not items_by_category:
            plan = _PHASE_PLANS.get(phase, _PHASE_PLANS[CyclePhase.follicular])
            foods = plan["recommended"]
            items_by_category = {
                "légumes et fruits": foods[:4],
                "protéines": foods[4:6] if len(foods) > 4 else [],
                "céréales et légumineuses": foods[6:] if len(foods) > 6 else [],
                "suppléments": plan["supplements"],
            }

        return ShoppingListResponse(
            week_start=date.today(),
            phase=phase.value,
            items_by_category=items_by_category,
            estimated_servings=14,
        )

    # ── AI nutrition coach ────────────────────────────────────────────────

    async def nutrition_coach(self, user: User, question: str, context: dict) -> NutritionCoachResponse:
        answer = "Je suis là pour vous accompagner dans votre alimentation hormonale."
        if self.ai_service is not None:
            try:
                ctx = {**context, "language": user.language}
                answer = await self.ai_service.nutrition_coach(question, ctx)
            except Exception:
                pass
        return NutritionCoachResponse(answer=answer)

    # ── Private helpers ───────────────────────────────────────────────────

    def _to_public(self, entity: NutritionLog) -> NutritionLogPublic:
        meals: list[str] = []
        raw_meals = decrypt_sensitive(entity.meals_encrypted)
        if raw_meals:
            try:
                meals = json.loads(raw_meals)
            except (json.JSONDecodeError, TypeError):
                meals = [raw_meals]

        return NutritionLogPublic(
            id=entity.id,
            user_id=entity.user_id,
            log_date=entity.log_date,
            meals=meals,
            hormonal_impact_score=entity.hormonal_impact_score,
            ai_analysis=decrypt_sensitive(entity.ai_analysis_encrypted),
            water_glasses=entity.water_glasses,
            notes=decrypt_sensitive(entity.notes_encrypted),
            created_at=entity.created_at,
        )

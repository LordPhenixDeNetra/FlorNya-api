from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_sensitive, encrypt_sensitive
from app.models.intimate_health_log import IntimateHealthLog
from app.models.libido_log import LibidoLog
from app.models.user import User
from app.repositories.intimate_repository import IntimateHealthRepository, LibidoRepository
from app.schemas.intimate import (
    ContraceptionMethod,
    IntimateHealthLogCreate,
    IntimateHealthLogPublic,
    LibidoLogCreate,
    LibidoLogPublic,
    SexualEducationContent,
    VaginalHealthInfo,
)
from app.services.ai.anthropic_service import AnthropicInsightService

_CONTRACEPTION_METHODS: list[ContraceptionMethod] = [
    ContraceptionMethod(id="pill", name="Pilule contraceptive", type="hormonal", effectiveness_pct=99.7,
        description="Contraceptif oral hormonal à prendre quotidiennement.",
        pros=["Très efficace", "Régule les cycles", "Réduit les douleurs menstruelles"],
        cons=["Prise quotidienne", "Effets hormonaux possibles", "Ne protège pas des IST"],
        suitable_for=["cycle_regulation", "dysmenorrhea"], requires_prescription=True),
    ContraceptionMethod(id="iud_hormonal", name="DIU hormonal (Mirena)", type="hormonal", effectiveness_pct=99.8,
        description="Stérilet hormonal inséré dans l'utérus. Efficace 5 ans.",
        pros=["Longue durée", "Réduit les règles voire les supprime", "Très efficace"],
        cons=["Insertion médicale", "Spotting les premiers mois"],
        suitable_for=["long_term", "dysmenorrhea"], requires_prescription=True),
    ContraceptionMethod(id="iud_copper", name="DIU cuivre", type="non_hormonal", effectiveness_pct=99.4,
        description="Stérilet en cuivre sans hormones. Efficace 5-10 ans.",
        pros=["Sans hormones", "Longue durée", "Contraception d'urgence possible"],
        cons=["Règles plus abondantes possible", "Crampes à l'insertion"],
        suitable_for=["hormone_free", "long_term"], requires_prescription=True),
    ContraceptionMethod(id="implant", name="Implant contraceptif", type="hormonal", effectiveness_pct=99.9,
        description="Petit bâtonnet inséré sous la peau du bras. Efficace 3 ans.",
        pros=["Très efficace", "Aucune prise quotidienne", "Réversible"],
        cons=["Insertion médicale", "Modification du cycle"],
        suitable_for=["long_term", "forgetful"], requires_prescription=True),
    ContraceptionMethod(id="condom", name="Préservatif masculin", type="barrier", effectiveness_pct=85.0,
        description="Contraceptif de barrière, seule méthode protégeant des IST.",
        pros=["Protège des IST", "Sans ordonnance", "Pas d'hormones"],
        cons=["Efficacité dépend de l'utilisation", "Peut réduire la spontanéité"],
        suitable_for=["ist_protection", "short_term"], requires_prescription=False),
    ContraceptionMethod(id="natural", name="Contraception naturelle (MAMA, calendrier)", type="natural", effectiveness_pct=76.0,
        description="Méthodes basées sur l'observation du cycle fertile.",
        pros=["Sans hormones", "Connaissance du corps", "Gratuit"],
        cons=["Efficacité moindre", "Demande de la rigueur", "Ne convient pas aux cycles irréguliers"],
        suitable_for=["hormone_free", "natural"], requires_prescription=False),
]

_VAGINAL_HEALTH_INFO = VaginalHealthInfo(
    discharge_guide=[
        {"type": "Transparent/blanc laiteux", "meaning": "Normal — flore vaginale saine"},
        {"type": "Blanc épais (fromage blanc)", "meaning": "Possible mycose — consulter si démangeaisons"},
        {"type": "Gris/vert/jaune avec odeur", "meaning": "Possible vaginose ou IST — consultation recommandée"},
        {"type": "Rose/marron", "meaning": "Spotting — normal autour de l'ovulation ou en début de règles"},
    ],
    infection_signs=["Odeur forte et inhabituelle", "Démangeaisons ou brûlures", "Douleurs pendant les rapports", "Écoulement inhabituel"],
    hygiene_tips=[
        "Nettoyage avec eau tiède seulement (l'intérieur est auto-nettoyant)",
        "Préférer les sous-vêtements en coton",
        "Essuyer de l'avant vers l'arrière",
        "Éviter les savons parfumés et douches vaginales",
        "Changer de tampon/protection toutes les 4-8 heures",
    ],
    when_to_consult=["Démangeaisons persistantes", "Douleurs pendant les rapports", "Saignements hors règles", "Écoulement verdâtre ou malodorant"],
)

_SEXUAL_ED_CONTENT: list[SexualEducationContent] = [
    SexualEducationContent(
        category="anatomie",
        title="Anatomie féminine",
        summary="Comprendre son corps : vulve, vagin, utérus, ovaires et clitoris.",
        key_points=["Le clitoris a 8 000 terminaisons nerveuses", "Le vagin est auto-nettoyant", "L'utérus change de taille selon le cycle"],
        age_group="18+",
    ),
    SexualEducationContent(
        category="plaisir",
        title="Le plaisir féminin",
        summary="Exploration du plaisir et de la sexualité selon les phases du cycle hormonal.",
        key_points=["La libido varie selon les phases hormonales", "L'ovulation correspond souvent au pic de libido", "La phase lutéale peut diminuer le désir"],
        age_group="18+",
    ),
    SexualEducationContent(
        category="consentement",
        title="Consentement et communication",
        summary="Les bases d'une sexualité épanouie et respectueuse.",
        key_points=["Le consentement est enthousiaste et révocable", "La communication ouverte améliore l'intimité", "Respectez vos limites et celles de l'autre"],
        age_group="13+",
    ),
    SexualEducationContent(
        category="sante",
        title="IST et prévention",
        summary="Infections Sexuellement Transmissibles : prévention et dépistage.",
        key_points=["Le préservatif est la seule protection contre les IST", "Dépistage régulier recommandé si partenaires multiples", "HPV : vaccination disponible jusqu'à 26 ans"],
        age_group="13+",
    ),
]


class IntimateService:
    def __init__(
        self,
        session: AsyncSession,
        libido_repo: LibidoRepository,
        intimate_repo: IntimateHealthRepository,
        ai_service: AnthropicInsightService | None = None,
    ):
        self.session = session
        self.libido_repo = libido_repo
        self.intimate_repo = intimate_repo
        self.ai_service = ai_service

    async def log_libido(self, user: User, data: LibidoLogCreate) -> LibidoLogPublic:
        entity = await self.libido_repo.upsert(
            user_id=user.id,
            log_date=data.log_date,
            score=data.score,
            notes_encrypted=encrypt_sensitive(data.notes),
        )
        await self.session.commit()
        await self.session.refresh(entity)
        return self._libido_to_public(entity)

    async def list_libido_logs(self, user: User, limit: int = 30) -> list[LibidoLogPublic]:
        entities = await self.libido_repo.list_by_user(user.id, limit=limit)
        return [self._libido_to_public(e) for e in entities]

    async def log_intimate_health(self, user: User, data: IntimateHealthLogCreate) -> IntimateHealthLogPublic:
        entity = await self.intimate_repo.upsert(
            user_id=user.id,
            log_date=data.log_date,
            vaginal_dryness_severity=data.vaginal_dryness_severity,
            discharge_type=data.discharge_type,
            pain_during_intercourse=data.pain_during_intercourse,
            pain_intensity=data.pain_intensity,
            itching=data.itching,
            notes_encrypted=encrypt_sensitive(data.notes),
        )
        await self.session.commit()
        await self.session.refresh(entity)
        return self._intimate_to_public(entity)

    async def list_intimate_health_logs(self, user: User, limit: int = 30) -> list[IntimateHealthLogPublic]:
        entities = await self.intimate_repo.list_by_user(user.id, limit=limit)
        return [self._intimate_to_public(e) for e in entities]

    def get_contraception_guide(self) -> list[ContraceptionMethod]:
        return _CONTRACEPTION_METHODS

    def get_vaginal_health_info(self) -> VaginalHealthInfo:
        return _VAGINAL_HEALTH_INFO

    def get_sexual_education(self, is_adult: bool = False) -> list[SexualEducationContent]:
        if is_adult:
            return _SEXUAL_ED_CONTENT
        return [c for c in _SEXUAL_ED_CONTENT if c.age_group == "13+"]

    async def get_intimate_advice(self, user: User, concern: str, cycle_phase: str = "follicular") -> str:
        from datetime import date as date_
        from app.core.security import is_adult as _is_adult
        if not _is_adult(user.date_of_birth):
            return "Ce contenu est réservé aux utilisatrices de 18 ans et plus."
        if not self.ai_service:
            return "Service IA non disponible."
        return await self.ai_service.intimate_health_advice(concern, {
            "language": user.language,
            "cycle_phase": cycle_phase,
            "is_adult": True,
        })

    def _libido_to_public(self, entity: LibidoLog) -> LibidoLogPublic:
        return LibidoLogPublic(
            id=entity.id,
            user_id=entity.user_id,
            log_date=entity.log_date,
            score=entity.score,
            notes=decrypt_sensitive(entity.notes_encrypted),
            created_at=entity.created_at,
        )

    def _intimate_to_public(self, entity: IntimateHealthLog) -> IntimateHealthLogPublic:
        return IntimateHealthLogPublic(
            id=entity.id,
            user_id=entity.user_id,
            log_date=entity.log_date,
            vaginal_dryness_severity=entity.vaginal_dryness_severity,
            discharge_type=entity.discharge_type.value if entity.discharge_type else None,
            pain_during_intercourse=entity.pain_during_intercourse,
            pain_intensity=entity.pain_intensity,
            itching=entity.itching,
            notes=decrypt_sensitive(entity.notes_encrypted),
            created_at=entity.created_at,
        )

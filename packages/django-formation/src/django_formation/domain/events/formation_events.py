from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class FormationEvent:
    name: str
    resource_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    actor_id: Optional[int] = None
    etablissement_id: Optional[str] = None


class FormationEventFactory:

    @staticmethod
    def apprenant_cree(apprenant_id: str, **kwargs) -> FormationEvent:
        return FormationEvent("apprenant_cree", apprenant_id, payload=kwargs)

    @staticmethod
    def apprenant_archive(apprenant_id: str, **kwargs) -> FormationEvent:
        return FormationEvent("apprenant_archive", apprenant_id, payload=kwargs)

    @staticmethod
    def formation_publiee(formation_id: str, **kwargs) -> FormationEvent:
        return FormationEvent("formation_publiee", formation_id, payload=kwargs)

    @staticmethod
    def formation_archivee(formation_id: str, **kwargs) -> FormationEvent:
        return FormationEvent("formation_archivee", formation_id, payload=kwargs)

    @staticmethod
    def session_inscriptions_ouvertes(session_id: str, **kwargs) -> FormationEvent:
        return FormationEvent("session_inscriptions_ouvertes", session_id, payload=kwargs)

    @staticmethod
    def session_demarre(session_id: str, **kwargs) -> FormationEvent:
        return FormationEvent("session_demarre", session_id, payload=kwargs)

    @staticmethod
    def session_terminee(session_id: str, **kwargs) -> FormationEvent:
        return FormationEvent("session_terminee", session_id, payload=kwargs)

    @staticmethod
    def session_annulee(session_id: str, **kwargs) -> FormationEvent:
        return FormationEvent("session_annulee", session_id, payload=kwargs)

    @staticmethod
    def inscription_creee(inscription_id: str, **kwargs) -> FormationEvent:
        return FormationEvent("inscription_creee", inscription_id, payload=kwargs)

    @staticmethod
    def inscription_confirmee(inscription_id: str, **kwargs) -> FormationEvent:
        return FormationEvent("inscription_confirmee", inscription_id, payload=kwargs)

    @staticmethod
    def inscription_refusee(inscription_id: str, **kwargs) -> FormationEvent:
        return FormationEvent("inscription_refusee", inscription_id, payload=kwargs)

    @staticmethod
    def inscription_annulee(inscription_id: str, **kwargs) -> FormationEvent:
        return FormationEvent("inscription_annulee", inscription_id, payload=kwargs)

    @staticmethod
    def inscription_abandonnee(inscription_id: str, **kwargs) -> FormationEvent:
        return FormationEvent("inscription_abandonnee", inscription_id, payload=kwargs)

    @staticmethod
    def inscription_terminee(inscription_id: str, **kwargs) -> FormationEvent:
        return FormationEvent("inscription_terminee", inscription_id, payload=kwargs)

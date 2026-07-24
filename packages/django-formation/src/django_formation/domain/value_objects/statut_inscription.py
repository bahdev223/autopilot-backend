from enum import Enum


class StatutInscription(Enum):
    PREINSCRITE = "PREINSCRITE"
    EN_ATTENTE = "EN_ATTENTE"
    CONFIRMEE = "CONFIRMEE"
    REFUSEE = "REFUSEE"
    ANNULEE = "ANNULEE"
    EN_COURS = "EN_COURS"
    ABANDONNEE = "ABANDONNEE"
    TERMINEE = "TERMINEE"

    @property
    def label(self) -> str:
        return _LABELS[self]

    def can_transition_to(self, target: "StatutInscription") -> bool:
        transitions = {
            StatutInscription.PREINSCRITE: {StatutInscription.EN_ATTENTE, StatutInscription.CONFIRMEE, StatutInscription.REFUSEE, StatutInscription.ANNULEE},
            StatutInscription.EN_ATTENTE: {StatutInscription.CONFIRMEE, StatutInscription.REFUSEE, StatutInscription.ANNULEE},
            StatutInscription.CONFIRMEE: {StatutInscription.EN_COURS, StatutInscription.ANNULEE},
            StatutInscription.EN_COURS: {StatutInscription.TERMINEE, StatutInscription.ABANDONNEE, StatutInscription.ANNULEE},
            StatutInscription.REFUSEE: set(),
            StatutInscription.ANNULEE: set(),
            StatutInscription.ABANDONNEE: set(),
            StatutInscription.TERMINEE: set(),
        }
        return target in transitions.get(self, set())

    def is_terminal(self) -> bool:
        return self in (StatutInscription.REFUSEE, StatutInscription.ANNULEE, StatutInscription.ABANDONNEE, StatutInscription.TERMINEE)

    def occupe_place(self) -> bool:
        return self in (
            StatutInscription.PREINSCRITE,
            StatutInscription.EN_ATTENTE,
            StatutInscription.CONFIRMEE,
            StatutInscription.EN_COURS,
        )


_LABELS = {
    StatutInscription.PREINSCRITE: "Préinscrite",
    StatutInscription.EN_ATTENTE: "En attente",
    StatutInscription.CONFIRMEE: "Confirmée",
    StatutInscription.REFUSEE: "Refusée",
    StatutInscription.ANNULEE: "Annulée",
    StatutInscription.EN_COURS: "En cours",
    StatutInscription.ABANDONNEE: "Abandonnée",
    StatutInscription.TERMINEE: "Terminée",
}

from enum import Enum


class StatutSession(Enum):
    BROUILLON = "BROUILLON"
    INSCRIPTIONS_OUVERTES = "INSCRIPTIONS_OUVERTES"
    INSCRIPTIONS_FERMEES = "INSCRIPTIONS_FERMEES"
    EN_COURS = "EN_COURS"
    TERMINEE = "TERMINEE"
    ANNULEE = "ANNULEE"

    @property
    def label(self) -> str:
        return _LABELS[self]

    def can_transition_to(self, target: "StatutSession") -> bool:
        transitions = {
            StatutSession.BROUILLON: {StatutSession.INSCRIPTIONS_OUVERTES, StatutSession.ANNULEE},
            StatutSession.INSCRIPTIONS_OUVERTES: {StatutSession.INSCRIPTIONS_FERMEES, StatutSession.EN_COURS, StatutSession.ANNULEE},
            StatutSession.INSCRIPTIONS_FERMEES: {StatutSession.INSCRIPTIONS_OUVERTES, StatutSession.EN_COURS, StatutSession.ANNULEE},
            StatutSession.EN_COURS: {StatutSession.TERMINEE, StatutSession.ANNULEE},
            StatutSession.TERMINEE: set(),
            StatutSession.ANNULEE: set(),
        }
        return target in transitions.get(self, set())

    def is_terminal(self) -> bool:
        return self in (StatutSession.TERMINEE, StatutSession.ANNULEE)

    def accepte_inscriptions(self) -> bool:
        return self == StatutSession.INSCRIPTIONS_OUVERTES


_LABELS = {
    StatutSession.BROUILLON: "Brouillon",
    StatutSession.INSCRIPTIONS_OUVERTES: "Inscriptions ouvertes",
    StatutSession.INSCRIPTIONS_FERMEES: "Inscriptions fermées",
    StatutSession.EN_COURS: "En cours",
    StatutSession.TERMINEE: "Terminée",
    StatutSession.ANNULEE: "Annulée",
}

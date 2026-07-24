from enum import Enum


class StatutFormation(Enum):
    BROUILLON = "BROUILLON"
    PUBLIEE = "PUBLIEE"
    SUSPENDUE = "SUSPENDUE"
    ARCHIVEE = "ARCHIVEE"

    @property
    def label(self) -> str:
        return _LABELS[self]

    def can_transition_to(self, target: "StatutFormation") -> bool:
        transitions = {
            StatutFormation.BROUILLON: {StatutFormation.PUBLIEE, StatutFormation.ARCHIVEE},
            StatutFormation.PUBLIEE: {StatutFormation.SUSPENDUE, StatutFormation.ARCHIVEE},
            StatutFormation.SUSPENDUE: {StatutFormation.PUBLIEE, StatutFormation.ARCHIVEE},
            StatutFormation.ARCHIVEE: set(),
        }
        return target in transitions.get(self, set())

    def is_terminal(self) -> bool:
        return self == StatutFormation.ARCHIVEE


_LABELS = {
    StatutFormation.BROUILLON: "Brouillon",
    StatutFormation.PUBLIEE: "Publiée",
    StatutFormation.SUSPENDUE: "Suspendue",
    StatutFormation.ARCHIVEE: "Archivée",
}

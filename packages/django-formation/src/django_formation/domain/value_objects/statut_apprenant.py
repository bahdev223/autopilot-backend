from enum import Enum


class StatutApprenant(Enum):
    ACTIF = "ACTIF"
    INACTIF = "INACTIF"
    ARCHIVE = "ARCHIVE"

    @property
    def label(self) -> str:
        return _LABELS[self]

    def can_transition_to(self, target: "StatutApprenant") -> bool:
        if self == StatutApprenant.ARCHIVE:
            return False
        if self == StatutApprenant.ACTIF and target == StatutApprenant.INACTIF:
            return True
        if self == StatutApprenant.INACTIF and target == StatutApprenant.ACTIF:
            return True
        if target == StatutApprenant.ARCHIVE:
            return True
        return False

    def is_terminal(self) -> bool:
        return self == StatutApprenant.ARCHIVE


_LABELS = {
    StatutApprenant.ACTIF: "Actif",
    StatutApprenant.INACTIF: "Inactif",
    StatutApprenant.ARCHIVE: "Archivé",
}

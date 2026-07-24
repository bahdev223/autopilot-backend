class FormationDomainError(Exception):
    code = "FORMATION_ERROR"
    status_code = 400

    def __init__(self, message="", code=None, status_code=None):
        super().__init__(message)
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code


class InactiveEstablishmentError(FormationDomainError):
    code = "ETABLISSEMENT_INACTIF"

    def __init__(self, message="L'établissement est inactif"):
        super().__init__(message)


class InactiveLearnerError(FormationDomainError):
    code = "APPRENANT_INACTIF"

    def __init__(self, message="L'apprenant est inactif"):
        super().__init__(message)


class ArchivedLearnerError(FormationDomainError):
    code = "APPRENANT_ARCHIVE"

    def __init__(self, message="L'apprenant est archivé"):
        super().__init__(message)


class ArchivedTrainingError(FormationDomainError):
    code = "FORMATION_ARCHIVEE"

    def __init__(self, message="La formation est archivée"):
        super().__init__(message)


class InvalidStatusTransitionError(FormationDomainError):
    code = "TRANSITION_INVALIDE"

    def __init__(self, current: str, target: str):
        super().__init__(f"Transition invalide de '{current}' vers '{target}'")


class SessionNotOpenError(FormationDomainError):
    code = "SESSION_FERMEE"

    def __init__(self, message="La session n'accepte pas les inscriptions"):
        super().__init__(message)


class SessionCapacityReachedError(FormationDomainError):
    code = "SESSION_COMPLETE"
    status_code = 409

    def __init__(self, message="La capacité maximale de la session est atteinte"):
        super().__init__(message)


class DuplicateEnrollmentError(FormationDomainError):
    code = "DOUBLON_INSCRIPTION"
    status_code = 409

    def __init__(self, message="Cet apprenant est déjà inscrit à cette session"):
        super().__init__(message)


class CrossEstablishmentOperationError(FormationDomainError):
    code = "ETABLISSEMENT_DIFFERENT"

    def __init__(self, message="Opération interdite entre différents établissements"):
        super().__init__(message)


class MissingRejectionReasonError(FormationDomainError):
    code = "MOTIF_REFUS_REQUIS"

    def __init__(self, message="Le motif de refus est obligatoire"):
        super().__init__(message)


class MissingCancellationReasonError(FormationDomainError):
    code = "MOTIF_ANNULATION_REQUIS"

    def __init__(self, message="Le motif d'annulation est obligatoire"):
        super().__init__(message)


class TrainingNotPublishedError(FormationDomainError):
    code = "FORMATION_NON_PUBLIEE"

    def __init__(self, message="La formation doit être publiée pour ouvrir les inscriptions"):
        super().__init__(message)


class NoConfirmedEnrollmentsError(FormationDomainError):
    code = "AUCUNE_INSCRIPTION_CONFIRMEE"

    def __init__(self, message="La session doit avoir au moins une inscription confirmée pour démarrer"):
        super().__init__(message)


class PendingEnrollmentsError(FormationDomainError):
    code = "INSCRIPTIONS_EN_ATTENTE"

    def __init__(self, message="Il reste des inscriptions en attente"):
        super().__init__(message)


class EstablishmentNotFoundError(FormationDomainError):
    code = "ETABLISSEMENT_INTROUVABLE"

    def __init__(self, message="Établissement introuvable"):
        super().__init__(message)


class LearnerNotFoundError(FormationDomainError):
    code = "APPRENANT_INTROUVABLE"

    def __init__(self, message="Apprenant introuvable"):
        super().__init__(message)


class TrainingNotFoundError(FormationDomainError):
    code = "FORMATION_INTROUVABLE"

    def __init__(self, message="Formation introuvable"):
        super().__init__(message)


class SessionNotFoundError(FormationDomainError):
    code = "SESSION_INTROUVABLE"

    def __init__(self, message="Session introuvable"):
        super().__init__(message)


class EnrollmentNotFoundError(FormationDomainError):
    code = "INSCRIPTION_INTROUVABLE"

    def __init__(self, message="Inscription introuvable"):
        super().__init__(message)

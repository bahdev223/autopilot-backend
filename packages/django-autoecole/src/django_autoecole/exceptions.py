class AutoEcoleDomainError(Exception):
    """Exception de base pour le domaine auto-école."""


class InactiveEstablishmentError(AutoEcoleDomainError):
    ...


class InvalidEnrollmentStatusError(AutoEcoleDomainError):
    ...


class InactivePermitCategoryError(AutoEcoleDomainError):
    ...


class DuplicateDrivingSchoolFileError(AutoEcoleDomainError):
    ...


class CrossEstablishmentOperationError(AutoEcoleDomainError):
    ...


class InstructorNotAuthorizedError(AutoEcoleDomainError):
    ...


class InstructorUnavailableError(AutoEcoleDomainError):
    ...


class VehicleUnavailableError(AutoEcoleDomainError):
    ...


class VehicleCategoryMismatchError(AutoEcoleDomainError):
    ...


class VehicleDocumentsExpiredError(AutoEcoleDomainError):
    ...


class LessonTimeConflictError(AutoEcoleDomainError):
    ...


class InvalidMileageError(AutoEcoleDomainError):
    ...


class InvalidStatusTransitionError(AutoEcoleDomainError):
    ...


class InsufficientTrainingHoursError(AutoEcoleDomainError):
    ...


class DossierNotExamReadyError(AutoEcoleDomainError):
    ...


class DuplicateActiveExamError(AutoEcoleDomainError):
    ...


class MissingCancellationReasonError(AutoEcoleDomainError):
    ...


class InvalidLessonDurationError(AutoEcoleDomainError):
    ...


class InvalidDateRangeError(AutoEcoleDomainError):
    ...

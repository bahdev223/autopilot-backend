from django.db import transaction
from django.utils import timezone

from django_formation.domain.exceptions.formation_exceptions import (
    InactiveEstablishmentError, ArchivedLearnerError, SessionNotOpenError,
    SessionCapacityReachedError, DuplicateEnrollmentError, CrossEstablishmentOperationError,
    MissingRejectionReasonError, MissingCancellationReasonError, InvalidStatusTransitionError,
)
from django_formation.domain.value_objects.statut_inscription import StatutInscription
from django_formation.models.apprenant import Apprenant
from django_formation.models.inscription import Inscription
from django_formation.models.session import SessionFormation
from django_formation.models.historique import HistoriqueStatutInscription
from django_formation.signals.formation_signals import (
    inscription_creee, inscription_confirmee, inscription_refusee,
    inscription_annulee, inscription_abandonnee, inscription_terminee,
)
from django_formation.settings import ENROLLMENT_NUMBER_PREFIX, get_number_generator


class InscriptionService:
    def _creer_historique(self, inscription: Inscription, ancien_statut: str, nouveau_statut: str, commentaire: str = "", modifie_par=None):
        HistoriqueStatutInscription.objects.create(
            inscription=inscription, ancien_statut=ancien_statut,
            nouveau_statut=nouveau_statut, commentaire=commentaire, modifie_par=modifie_par,
        )

    @transaction.atomic
    def creer_preinscription(self, *, apprenant: Apprenant, session: SessionFormation, commentaire: str = "", cree_par=None) -> Inscription:
        session = SessionFormation.objects.select_for_update().select_related("etablissement", "formation").get(pk=session.pk)
        if not session.etablissement.actif:
            raise InactiveEstablishmentError()
        if apprenant.statut == Apprenant.Statut.ARCHIVE:
            raise ArchivedLearnerError()
        if apprenant.etablissement_id != session.etablissement_id:
            raise CrossEstablishmentOperationError("L'apprenant et la session doivent appartenir au même établissement")
        if not session.accepte_inscriptions:
            raise SessionNotOpenError()
        if Inscription.objects.filter(apprenant=apprenant, session=session).exists():
            raise DuplicateEnrollmentError()
        if session.capacite is not None and session.nombre_inscrits_actifs >= session.capacite:
            raise SessionCapacityReachedError()
        generator = get_number_generator("ENROLLMENT_NUMBER_GENERATOR")
        numero = generator(
            queryset=Inscription.objects.filter(etablissement=session.etablissement),
            prefix=ENROLLMENT_NUMBER_PREFIX,
        )
        inscription = Inscription.objects.create(
            etablissement=session.etablissement, apprenant=apprenant,
            session=session, numero=numero, date_inscription=timezone.localdate(),
            statut=Inscription.Statut.PREINSCRITE, commentaire=commentaire,
        )
        self._creer_historique(inscription, "", "PREINSCRITE", "Préinscription créée", cree_par)
        transaction.on_commit(
            lambda: inscription_creee.send(
                sender=self.__class__, inscription=inscription, cree_par=cree_par
            )
        )
        return inscription

    def _effectuer_transition(self, inscription: Inscription, nouveau_statut: str, modifie_par=None, **kwargs) -> Inscription:
        ancien = inscription.statut
        statut_enum = StatutInscription(ancien)
        if not statut_enum.can_transition_to(StatutInscription(nouveau_statut)):
            raise InvalidStatusTransitionError(ancien, nouveau_statut)
        inscription.statut = nouveau_statut
        for field, value in kwargs.items():
            if hasattr(inscription, field):
                setattr(inscription, field, value)
        if nouveau_statut == "CONFIRMEE":
            inscription.date_confirmation = timezone.now()
        if nouveau_statut in ("TERMINEE", "ABANDONNEE"):
            inscription.date_fin = timezone.now()
        inscription.save()
        self._creer_historique(inscription, ancien, nouveau_statut, modifie_par=modifie_par)
        return inscription

    @transaction.atomic
    def mettre_en_attente(self, inscription: Inscription, modifie_par=None) -> Inscription:
        return self._effectuer_transition(inscription, "EN_ATTENTE", modifie_par)

    @transaction.atomic
    def confirmer_inscription(self, inscription: Inscription, modifie_par=None) -> Inscription:
        result = self._effectuer_transition(inscription, "CONFIRMEE", modifie_par)
        transaction.on_commit(
            lambda: inscription_confirmee.send(
                sender=self.__class__, inscription=result, confirme_par=modifie_par
            )
        )
        return result

    @transaction.atomic
    def refuser_inscription(self, inscription: Inscription, motif: str, modifie_par=None) -> Inscription:
        if not motif:
            raise MissingRejectionReasonError()
        result = self._effectuer_transition(inscription, "REFUSEE", modifie_par, motif_refus=motif)
        transaction.on_commit(
            lambda: inscription_refusee.send(sender=self.__class__, inscription=result, motif=motif)
        )
        return result

    @transaction.atomic
    def annuler_inscription(self, inscription: Inscription, motif: str, modifie_par=None) -> Inscription:
        if not motif:
            raise MissingCancellationReasonError()
        result = self._effectuer_transition(inscription, "ANNULEE", modifie_par, motif_annulation=motif)
        transaction.on_commit(
            lambda: inscription_annulee.send(sender=self.__class__, inscription=result, motif=motif)
        )
        return result

    @transaction.atomic
    def demarrer_inscription(self, inscription: Inscription, modifie_par=None) -> Inscription:
        return self._effectuer_transition(inscription, "EN_COURS", modifie_par)

    @transaction.atomic
    def marquer_abandon(self, inscription: Inscription, modifie_par=None) -> Inscription:
        result = self._effectuer_transition(inscription, "ABANDONNEE", modifie_par)
        transaction.on_commit(
            lambda: inscription_abandonnee.send(sender=self.__class__, inscription=result)
        )
        return result

    @transaction.atomic
    def terminer_inscription(self, inscription: Inscription, modifie_par=None) -> Inscription:
        result = self._effectuer_transition(inscription, "TERMINEE", modifie_par)
        transaction.on_commit(
            lambda: inscription_terminee.send(sender=self.__class__, inscription=result)
        )
        return result

from datetime import date

from django.db import transaction

from django_formation.domain.exceptions.formation_exceptions import (
    InactiveEstablishmentError, ArchivedTrainingError, InvalidStatusTransitionError,
    TrainingNotPublishedError, NoConfirmedEnrollmentsError, PendingEnrollmentsError,
    CrossEstablishmentOperationError,
)
from django_formation.domain.value_objects.statut_session import StatutSession
from django_formation.domain.validators.formation_validator import FormationValidator
from django_formation.models.etablissement import Etablissement
from django_formation.models.formation import Formation
from django_formation.models.session import SessionFormation
from django_formation.models.inscription import Inscription
from django_formation.models.historique import HistoriqueStatutInscription
from django_formation.signals.formation_signals import (
    session_inscriptions_ouvertes, session_demarre, session_terminee, session_annulee,
    inscription_demarre, inscription_annulee,
)


class SessionService:
    @transaction.atomic
    def creer_session(self, *, etablissement: Etablissement, formation: Formation, code: str, nom: str, date_debut: date, **kwargs) -> SessionFormation:
        if not etablissement.actif:
            raise InactiveEstablishmentError()
        if formation.etablissement_id != etablissement.id:
            raise CrossEstablishmentOperationError("La formation n'appartient pas à cet établissement")
        if formation.statut == Formation.Statut.ARCHIVEE:
            raise ArchivedTrainingError()
        FormationValidator.valider_dates(date_debut, kwargs.get("date_fin"))
        FormationValidator.valider_periodes_inscription(
            kwargs.get("date_ouverture_inscriptions"),
            kwargs.get("date_fermeture_inscriptions"),
        )
        FormationValidator.valider_capacite(kwargs.get("capacite"))
        FormationValidator.valider_tarif(kwargs.get("tarif"))
        session = SessionFormation.objects.create(
            etablissement=etablissement, formation=formation,
            code=code, nom=nom, date_debut=date_debut, **kwargs,
        )
        return session

    @transaction.atomic
    def modifier_session(self, session: SessionFormation, **kwargs) -> SessionFormation:
        FormationValidator.valider_dates(
            kwargs.get("date_debut", session.date_debut),
            kwargs.get("date_fin", session.date_fin),
        )
        FormationValidator.valider_periodes_inscription(
            kwargs.get("date_ouverture_inscriptions", session.date_ouverture_inscriptions),
            kwargs.get("date_fermeture_inscriptions", session.date_fermeture_inscriptions),
        )
        FormationValidator.valider_capacite(kwargs.get("capacite", session.capacite))
        FormationValidator.valider_tarif(kwargs.get("tarif", session.tarif))
        for field, value in kwargs.items():
            if hasattr(session, field):
                setattr(session, field, value)
        session.save()
        return session

    @transaction.atomic
    def ouvrir_inscriptions(self, session: SessionFormation) -> SessionFormation:
        if not StatutSession(session.statut).can_transition_to(StatutSession.INSCRIPTIONS_OUVERTES):
            raise InvalidStatusTransitionError(session.statut, "INSCRIPTIONS_OUVERTES")
        if session.formation.statut != Formation.Statut.PUBLIEE:
            raise TrainingNotPublishedError()
        session.statut = SessionFormation.Statut.INSCRIPTIONS_OUVERTES
        session.save(update_fields=["statut"])
        transaction.on_commit(
            lambda: session_inscriptions_ouvertes.send(sender=self.__class__, session=session)
        )
        return session

    @transaction.atomic
    def fermer_inscriptions(self, session: SessionFormation) -> SessionFormation:
        if not StatutSession(session.statut).can_transition_to(StatutSession.INSCRIPTIONS_FERMEES):
            raise InvalidStatusTransitionError(session.statut, "INSCRIPTIONS_FERMEES")
        session.statut = SessionFormation.Statut.INSCRIPTIONS_FERMEES
        session.save(update_fields=["statut"])
        return session

    @transaction.atomic
    def demarrer_session(self, session: SessionFormation, modifie_par=None) -> SessionFormation:
        if not StatutSession(session.statut).can_transition_to(StatutSession.EN_COURS):
            raise InvalidStatusTransitionError(session.statut, "EN_COURS")
        inscriptions = session.inscriptions.select_for_update().filter(statut=Inscription.Statut.CONFIRMEE)
        if inscriptions.count() == 0:
            raise NoConfirmedEnrollmentsError()
        for inscription_obj in inscriptions:
            ancien = inscription_obj.statut
            inscription_obj.statut = Inscription.Statut.EN_COURS
            inscription_obj.save(update_fields=["statut"])
            HistoriqueStatutInscription.objects.create(
                inscription=inscription_obj, ancien_statut=ancien,
                nouveau_statut="EN_COURS", modifie_par=modifie_par,
            )
            transaction.on_commit(
                lambda inscription=inscription_obj: inscription_demarre.send(  # type: ignore[misc]
                    sender=self.__class__, inscription=inscription
                )
            )
        session.statut = SessionFormation.Statut.EN_COURS
        session.save(update_fields=["statut"])
        transaction.on_commit(lambda: session_demarre.send(sender=self.__class__, session=session))
        return session

    @transaction.atomic
    def terminer_session(self, session: SessionFormation, modifie_par=None) -> SessionFormation:
        if not StatutSession(session.statut).can_transition_to(StatutSession.TERMINEE):
            raise InvalidStatusTransitionError(session.statut, "TERMINEE")
        pending = session.inscriptions.filter(statut__in=["PREINSCRITE", "EN_ATTENTE"]).count()
        if pending > 0:
            raise PendingEnrollmentsError(f"Il reste {pending} inscription(s) en attente")
        session.statut = SessionFormation.Statut.TERMINEE
        session.save(update_fields=["statut"])
        transaction.on_commit(lambda: session_terminee.send(sender=self.__class__, session=session))
        return session

    @transaction.atomic
    def annuler_session(self, session: SessionFormation, modifie_par=None) -> SessionFormation:
        if not StatutSession(session.statut).can_transition_to(StatutSession.ANNULEE):
            raise InvalidStatusTransitionError(session.statut, "ANNULEE")
        inscriptions = session.inscriptions.select_for_update().filter(
            statut__in=["PREINSCRITE", "EN_ATTENTE", "CONFIRMEE", "EN_COURS"],
        )
        for inscription_obj in inscriptions:
            ancien = inscription_obj.statut
            inscription_obj.statut = Inscription.Statut.ANNULEE
            inscription_obj.motif_annulation = "Session annulée"
            inscription_obj.save(update_fields=["statut", "motif_annulation"])
            HistoriqueStatutInscription.objects.create(
                inscription=inscription_obj, ancien_statut=ancien,
                nouveau_statut="ANNULEE", commentaire="Session annulée",
                modifie_par=modifie_par,
            )
            transaction.on_commit(
                lambda inscription=inscription_obj: inscription_annulee.send(  # type: ignore[misc]
                    sender=self.__class__, inscription=inscription
                )
            )
        session.statut = SessionFormation.Statut.ANNULEE
        session.save(update_fields=["statut"])
        transaction.on_commit(lambda: session_annulee.send(sender=self.__class__, session=session))
        return session

from django.db import transaction

from django_formation.domain.exceptions.formation_exceptions import (
    InactiveEstablishmentError, InvalidStatusTransitionError,
)
from django_formation.domain.value_objects.statut_formation import StatutFormation
from django_formation.models.etablissement import Etablissement
from django_formation.models.formation import Formation
from django_formation.signals.formation_signals import formation_publiee, formation_archivee
from django_formation.domain.validators.formation_validator import FormationValidator


class FormationService:
    @transaction.atomic
    def creer_formation(self, *, etablissement: Etablissement, code: str, nom: str, **kwargs) -> Formation:
        if not etablissement.actif:
            raise InactiveEstablishmentError()
        FormationValidator.valider_duree(kwargs.get("duree_heures"))
        FormationValidator.valider_duree(kwargs.get("duree_jours"))
        FormationValidator.valider_tarif(kwargs.get("tarif_indicatif"))
        formation = Formation.objects.create(etablissement=etablissement, code=code, nom=nom, **kwargs)
        return formation

    @transaction.atomic
    def modifier_formation(self, formation: Formation, **kwargs) -> Formation:
        FormationValidator.valider_duree(kwargs.get("duree_heures", formation.duree_heures))
        FormationValidator.valider_duree(kwargs.get("duree_jours", formation.duree_jours))
        FormationValidator.valider_tarif(kwargs.get("tarif_indicatif", formation.tarif_indicatif))
        for field, value in kwargs.items():
            if hasattr(formation, field):
                setattr(formation, field, value)
        formation.save()
        return formation

    @transaction.atomic
    def publier_formation(self, formation: Formation) -> Formation:
        if not StatutFormation(formation.statut).can_transition_to(StatutFormation.PUBLIEE):
            raise InvalidStatusTransitionError(formation.statut, "PUBLIEE")
        if not formation.etablissement.actif:
            raise InactiveEstablishmentError()
        formation.statut = Formation.Statut.PUBLIEE
        formation.save(update_fields=["statut"])
        transaction.on_commit(
            lambda: formation_publiee.send(sender=self.__class__, formation=formation)
        )
        return formation

    @transaction.atomic
    def suspendre_formation(self, formation: Formation) -> Formation:
        if not StatutFormation(formation.statut).can_transition_to(StatutFormation.SUSPENDUE):
            raise InvalidStatusTransitionError(formation.statut, "SUSPENDUE")
        formation.statut = Formation.Statut.SUSPENDUE
        formation.save(update_fields=["statut"])
        return formation

    @transaction.atomic
    def reactiver_formation(self, formation: Formation) -> Formation:
        if not StatutFormation(formation.statut).can_transition_to(StatutFormation.PUBLIEE):
            raise InvalidStatusTransitionError(formation.statut, "PUBLIEE")
        formation.statut = Formation.Statut.PUBLIEE
        formation.save(update_fields=["statut"])
        return formation

    @transaction.atomic
    def archiver_formation(self, formation: Formation) -> Formation:
        if not StatutFormation(formation.statut).can_transition_to(StatutFormation.ARCHIVEE):
            raise InvalidStatusTransitionError(formation.statut, "ARCHIVEE")
        formation.statut = Formation.Statut.ARCHIVEE
        formation.save(update_fields=["statut"])
        transaction.on_commit(
            lambda: formation_archivee.send(sender=self.__class__, formation=formation)
        )
        return formation

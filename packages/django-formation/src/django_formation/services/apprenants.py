from typing import Optional

from django.db import transaction

from django_formation.domain.exceptions.formation_exceptions import (
    InactiveEstablishmentError, InvalidStatusTransitionError,
)
from django_formation.domain.value_objects.statut_apprenant import StatutApprenant
from django_formation.models.apprenant import Apprenant
from django_formation.models.etablissement import Etablissement
from django_formation.settings import LEARNER_NUMBER_PREFIX, get_number_generator
from django_formation.signals.formation_signals import apprenant_cree, apprenant_archive


class ApprenantService:
    @transaction.atomic
    def creer_apprenant(
        self, *, etablissement: Etablissement, nom: str, prenom: str,
        matricule: Optional[str] = None, utilisateur=None,
        telephone: str = "", email: str = "", cree_par=None, **kwargs,
    ) -> Apprenant:
        if not etablissement.actif:
            raise InactiveEstablishmentError()
        etablissement = Etablissement.objects.select_for_update().get(pk=etablissement.pk)
        if not matricule:
            generator = get_number_generator("LEARNER_NUMBER_GENERATOR")
            matricule = generator(
                queryset=Apprenant.objects.filter(etablissement=etablissement),
                prefix=LEARNER_NUMBER_PREFIX,
            )
        apprenant = Apprenant.objects.create(
            etablissement=etablissement, matricule=matricule,
            nom=nom.strip().upper(), prenom=prenom.strip().capitalize(),
            utilisateur=utilisateur, telephone=telephone, email=email, **kwargs,
        )
        transaction.on_commit(
            lambda: apprenant_cree.send(sender=self.__class__, apprenant=apprenant, cree_par=cree_par)
        )
        return apprenant

    @transaction.atomic
    def modifier_apprenant(self, apprenant: Apprenant, **kwargs) -> Apprenant:
        for field, value in kwargs.items():
            if hasattr(apprenant, field):
                setattr(apprenant, field, value)
        apprenant.save()
        return apprenant

    @transaction.atomic
    def activer_apprenant(self, apprenant: Apprenant) -> Apprenant:
        if not StatutApprenant(apprenant.statut).can_transition_to(StatutApprenant.ACTIF):
            raise InvalidStatusTransitionError(apprenant.statut, "ACTIF")
        apprenant.statut = Apprenant.Statut.ACTIF
        apprenant.save(update_fields=["statut"])
        return apprenant

    @transaction.atomic
    def desactiver_apprenant(self, apprenant: Apprenant) -> Apprenant:
        if not StatutApprenant(apprenant.statut).can_transition_to(StatutApprenant.INACTIF):
            raise InvalidStatusTransitionError(apprenant.statut, "INACTIF")
        apprenant.statut = Apprenant.Statut.INACTIF
        apprenant.save(update_fields=["statut"])
        return apprenant

    @transaction.atomic
    def archiver_apprenant(self, apprenant: Apprenant) -> Apprenant:
        if not StatutApprenant(apprenant.statut).can_transition_to(StatutApprenant.ARCHIVE):
            raise InvalidStatusTransitionError(apprenant.statut, "ARCHIVE")
        apprenant.statut = Apprenant.Statut.ARCHIVE
        apprenant.save(update_fields=["statut"])
        transaction.on_commit(
            lambda: apprenant_archive.send(sender=self.__class__, apprenant=apprenant)
        )
        return apprenant

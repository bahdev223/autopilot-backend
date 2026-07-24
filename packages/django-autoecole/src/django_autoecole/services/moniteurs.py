from django.db import transaction
from django_autoecole.models import Moniteur
from django_autoecole.constants import StatutMoniteur
from django_autoecole.exceptions import (
    CrossEstablishmentOperationError, AutoEcoleDomainError,
)
from django_autoecole import signals


def _lock_moniteur(moniteur):
    Moniteur.objects.filter(pk=moniteur.pk).select_for_update()
    moniteur.refresh_from_db()


@transaction.atomic
def creer_moniteur(*, etablissement, matricule, nom, prenom, telephone="",
                    email="", numero_agrement="", date_embauche=None, cree_par=None):
    moniteur = Moniteur.objects.create(
        etablissement=etablissement,
        matricule=matricule,
        nom=nom,
        prenom=prenom,
        telephone=telephone,
        email=email,
        numero_agrement=numero_agrement,
        date_embauche=date_embauche,
        statut=StatutMoniteur.ACTIF,
    )
    signals.emit_on_commit(signals.moniteur_cree, creer_moniteur, moniteur=moniteur, cree_par=cree_par)
    return moniteur


@transaction.atomic
def modifier_moniteur(moniteur, **data):
    _lock_moniteur(moniteur)
    for field in ("nom", "prenom", "telephone", "email", "numero_agrement", "date_embauche"):
        if field in data:
            setattr(moniteur, field, data[field])
    moniteur.save(update_fields=list(data.keys()) + ["updated_at"])
    signals.emit_on_commit(signals.moniteur_modifie, modifier_moniteur, moniteur=moniteur)
    return moniteur


@transaction.atomic
def activer_moniteur(moniteur):
    _lock_moniteur(moniteur)
    moniteur.statut = StatutMoniteur.ACTIF
    moniteur.save(update_fields=["statut", "updated_at"])
    signals.emit_on_commit(signals.moniteur_active, activer_moniteur, moniteur=moniteur)
    return moniteur


@transaction.atomic
def rendre_moniteur_indisponible(moniteur):
    _lock_moniteur(moniteur)
    moniteur.statut = StatutMoniteur.INDISPONIBLE
    moniteur.save(update_fields=["statut", "updated_at"])
    signals.emit_on_commit(signals.moniteur_indisponible, rendre_moniteur_indisponible, moniteur=moniteur)
    return moniteur


@transaction.atomic
def suspendre_moniteur(moniteur):
    _lock_moniteur(moniteur)
    moniteur.statut = StatutMoniteur.SUSPENDU
    moniteur.save(update_fields=["statut", "updated_at"])
    signals.emit_on_commit(signals.moniteur_suspendu, suspendre_moniteur, moniteur=moniteur)
    return moniteur


@transaction.atomic
def reactiver_moniteur(moniteur):
    _lock_moniteur(moniteur)
    moniteur.statut = StatutMoniteur.ACTIF
    moniteur.save(update_fields=["statut", "updated_at"])
    signals.emit_on_commit(signals.moniteur_reactive, reactiver_moniteur, moniteur=moniteur)
    return moniteur


@transaction.atomic
def archiver_moniteur(moniteur):
    _lock_moniteur(moniteur)
    from django_autoecole.constants import StatutLecon
    if moniteur.lecons.filter(statut__in=[StatutLecon.EN_COURS, StatutLecon.CONFIRMEE]).exists():
        raise AutoEcoleDomainError("Impossible d'archiver un moniteur avec des leçons en cours")
    moniteur.statut = StatutMoniteur.ARCHIVE
    moniteur.save(update_fields=["statut", "updated_at"])
    signals.emit_on_commit(signals.moniteur_archive, archiver_moniteur, moniteur=moniteur)
    return moniteur


@transaction.atomic
def ajouter_habilitation_permis(moniteur, categorie_permis):
    _lock_moniteur(moniteur)
    if categorie_permis.etablissement_id != moniteur.etablissement_id:
        raise CrossEstablishmentOperationError("La catégorie n'appartient pas au même établissement")
    moniteur.categories_permis.add(categorie_permis)
    signals.emit_on_commit(signals.habilitation_permis_ajoutee, ajouter_habilitation_permis, moniteur=moniteur, categorie_permis=categorie_permis)
    return moniteur


@transaction.atomic
def retirer_habilitation_permis(moniteur, categorie_permis):
    _lock_moniteur(moniteur)
    moniteur.categories_permis.remove(categorie_permis)
    signals.emit_on_commit(signals.habilitation_permis_retiree, retirer_habilitation_permis, moniteur=moniteur, categorie_permis=categorie_permis)
    return moniteur
